# uv run -m pytest tests/interfaces/test_operation_flow.py
# uv run -m pytest tests/interfaces/test_operation_flow.py::test_register_duplicate_student_id -s
from types import SimpleNamespace
import pytest

from application.check_score_service import CheckScoreService
from domain.event_log import EventEnum
from domain.user_state import UserStateEnum
from tests.helpers import (ev_follow, ev_message_text, ev_postback,
                           make_base_envelope, post_line_event)


class FakeMoodleRepo:
    """最小可行的 Moodle stub，符合 RegistrationService 會用到的兩個方法。"""

    def __init__(self, *, student_id: str, fullname: str, course_fullname: str, roleid: int = 5, user_id: int = 999):
        self._student_id = student_id
        self._fullname = fullname
        self._course_fullname = course_fullname
        self._roleid = roleid
        self._user_id = user_id

    def find_student_info(self, student_id: str):
        # 回傳類似 Enrollment 的東西，只要屬性名字對得上就行
        if student_id == self._student_id:
            return SimpleNamespace(
                user_id=self._user_id,
                fullname=self._fullname,
                course_fullname=self._course_fullname,
                roleid=self._roleid,
            )
        return None

    def find_student_enrollments(self, student_id: str):
        # 回傳多門課也行；至少包含你在 MySQL 中 seed 的那一門
        if student_id != self._student_id:
            return []
        return [
            SimpleNamespace(
                user_id=self._user_id,
                fullname=self._fullname,
                course_fullname=self._course_fullname,
                roleid=self._roleid,
            )
        ]


@pytest.fixture
def fetch_leave(linebot_mysql_truncate):
    """提供一個 callable：fetch_leave(student_id) -> dict | None"""
    conn = linebot_mysql_truncate

    def _fetch(student_id):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT operation_time, student_ID, student_name, apply_time, reason, context_title
                FROM ask_for_leave
                WHERE student_ID = %s
                ORDER BY operation_time DESC
                LIMIT 1
                """,
                (student_id,),
            )
            return cur.fetchone()
    return _fetch


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_register_success(client, app, container, seed_course_commit):
    """
    Scenario: 成功註冊與綁定課程
    Given 我是尚未註冊的新學生
    When 我輸入正確的學號
    Then 系統應該確認該學號尚未被註冊
    And 系統應該查詢我所屬的課程
    And 系統應該綁定我的 LINE 帳號與課程
    And 系統應該回應歡迎訊息
    And 系統應該切換選單畫面到主選單
    """

    # 這門課要與 FakeMoodleRepo 回傳的 course_fullname 完全一致
    course_title = "1234_程式設計-Python_黃鈺晴教師"
    seed_course_commit(context_title=course_title)

    # 準備假 Moodle + 假 Line service
    student_id = "112522065"
    fullname = "測試學生"
    fake_moodle = FakeMoodleRepo(
        student_id=student_id, fullname=fullname, course_fullname=course_title)

    with container.moodle_repo.override(fake_moodle):
        # 1) 使用者加入好友
        payload = make_base_envelope(ev_follow(user_id="test_id"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

        # 2) 使用者輸入學號 → 觸發註冊流程
        payload = make_base_envelope(ev_message_text(
            text=student_id, user_id="test_id"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    # 驗證資料庫真的寫入
    student_repo = container.student_repo()
    student = student_repo.find_by_line_id("test_id")
    assert student is not None
    assert student.student_id == student_id
    assert student.name == fullname
    assert student.context_title == course_title


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_register_duplicate_student_id(client, app, container, seed_student_commit, seed_course_commit, line_api_service_spy):
    """
    學號已被綁：student_repo.find_by_student_id 有人 → 應回覆「已被使用」
    """
    # Arrange: 先種一門與 Moodle stub 對得上的課
    course_title = "1234_程式設計-Python_黃鈺晴教師"
    seed_course_commit(context_title=course_title)

    # 已有綁定的學生
    existing = seed_student_commit(
        user_id="U_already_bound",
        student_id="112522065",
        name="已綁學生",
        context_title=course_title
    )

    # 準備 FakeMoodleRepo（即使應該先擋重複，也保持依賴一致）
    fake_moodle = FakeMoodleRepo(
        student_id=existing["student_id"],
        fullname="測試學生",
        course_fullname=course_title
    )

    # Act: 另一個 LINE 使用者用相同學號嘗試註冊
    new_user_line_id = "U_new_user"
    with container.moodle_repo.override(fake_moodle):
        payload = make_base_envelope(ev_follow(new_user_line_id))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

        payload = make_base_envelope(ev_message_text(
            existing["student_id"], user_id=new_user_line_id))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    # Assert: 回覆含「已被使用」；且不會把新 user_id 寫進 DB
    assert any("此學號已被其他 Line 帳號使用，請洽詢助教。" in r["text"]
               for r in line_api_service_spy.replies)

    student_repo = container.student_repo()
    assert student_repo.find_by_line_id(new_user_line_id) is None


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_register_moodle_not_found(client, app, container, seed_course_commit, line_api_service_spy, chatbot_logger_spy):
    """
    Moodle 查無此人：find_student_info=None → 正確提示，不寫 DB
    """
    # Arrange
    course_title = "5678_資料結構_王老師"
    seed_course_commit(context_title=course_title)

    line_user_id = "U_not_found"

    # 用「不相等的學號」讓 FakeMoodleRepo 回傳 None
    fake_moodle = FakeMoodleRepo(
        student_id="000000000",                # 與使用者輸入不同 → find_student_info 會回 None
        fullname="隨便人名",
        course_fullname=course_title
    )

    with container.moodle_repo.override(fake_moodle):

        # Act: follow then input unknown id
        resp, _ = post_line_event(
            client, app, make_base_envelope(ev_follow(line_user_id)))
        assert resp.status_code == 200

        resp, _ = post_line_event(
            client, app,
            make_base_envelope(ev_message_text(
                "999999999", user_id=line_user_id))
        )
        assert resp.status_code == 200

    # Assert: 正確提示 & 不寫入 DB & 不記 REGISTER
    assert any(("在教學平台上找不到這個學號，請確認後再試一次。" in r["text"])
               for r in line_api_service_spy.replies)

    student_repo = container.student_repo()
    assert student_repo.find_by_line_id(line_user_id) is None

    assert not any(e.get("event_type") ==
                   EventEnum.REGISTER for e in chatbot_logger_spy.events)


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_register_with_emoji_name_ok(client, app, container, seed_course_commit):
    """
    姓名/課名包含 emoji/中英混雜：確保寫入不炸（回測一個包含 emoji 的名子）
    """
    # Arrange
    course_title = "2468_演算法🧩與實作_李老師"
    seed_course_commit(context_title=course_title)

    line_user_id = "U_emoji"
    student_id = "101010101"
    fullname = "小丸子😊"

    fake_moodle = FakeMoodleRepo(
        student_id=student_id,
        fullname=fullname,
        course_fullname=course_title
    )

    with container.moodle_repo.override(fake_moodle):

        # Act
        resp, _ = post_line_event(
            client, app, make_base_envelope(ev_follow(line_user_id)))
        assert resp.status_code == 200

        resp, _ = post_line_event(
            client, app,
            make_base_envelope(ev_message_text(
                student_id, user_id=line_user_id))
        )
        assert resp.status_code == 200

    student_repo = container.student_repo()
    s = student_repo.find_by_line_id(line_user_id)
    assert s is not None
    assert s.student_id == student_id
    assert s.name == fullname
    assert s.context_title == course_title


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_follow_again_already_registered_only_switch_menu(client, app, container, seed_student_commit, seed_course_commit, line_api_service_spy, chatbot_logger_spy):
    """
    後續 follow（已註冊）：再次 follow → 只切 RichMenu 不重註冊。
    """
    # Arrange: pre-registered student
    course_title = "1357_AI程式設計_張老師"
    seed_course_commit(context_title=course_title)

    student = seed_student_commit(
        user_id="U_registered",          # 與 duplicate 測試一致，使用 user_id 參數名
        student_id="114514000",
        name="小智",
        context_title=course_title
    )

    # Act: the same user follows again
    resp, _ = post_line_event(client, app, make_base_envelope(ev_follow(
        student["line_user_id"] if "line_user_id" in student else student["user_id"])))
    assert resp.status_code == 200

    # Assert: rich menu was linked, no new REGISTER event, and no duplicate welcome text
    target_user = student.get("line_user_id", student["user_id"])
    assert any(x["menu_alias"] == "main" and x["user_id"] ==
               target_user for x in line_api_service_spy.linked)
    assert not any(e.get("event_type") ==
                   EventEnum.REGISTER for e in chatbot_logger_spy.events)
    assert not any("很高興認識你" in r["text"] for r in line_api_service_spy.replies)


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_leave_full_flow(client, app, container, seed_student_commit, mail_spy, leave_repo_spy, fetch_leave):
    """
    Scenario: 成功完成請假申請
    Given 我已經註冊並登入系統
    And 我開啟了 Pychatbot 主選單
    When 我點選「請假」按鈕
    And 我確認要在下次課程請假
    And 我輸入請假原因為「身體不適」
    Then 系統應該記錄我的請假資料
    And 系統應該傳送「請假完成」的訊息給我
    And 系統應該通知助教我的請假訊息（若課程設有通知）
    期望: 資料庫 MySQLLeaveRepository 有對應的請假紀錄
    """
    context_title = "1234_程式設計-Python_黃鈺晴教師"
    stu = seed_student_commit(
        context_title=context_title, user_id="U_TEST_USER_ID")
    line_user_id = stu["user_id"]
    student_id = stu["student_id"]
    reason_text = "生病"

    user_state = container.user_state_accessor()

    # Act：1) 點【請假】
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback("apply_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 2) 確認請假 → 進入 AWAITING_LEAVE_REASON
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback(
            "[Action]confirm_to_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200
    assert user_state.get_state(
        line_user_id) == UserStateEnum.AWAITING_LEAVE_REASON

    # 3) 輸入理由 → 回到 IDLE，寫入 DB，並（若課程開啟）寄信
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_message_text(
            text=reason_text, user_id=line_user_id))
    )
    assert resp.status_code == 200
    assert user_state.get_state(line_user_id) == UserStateEnum.IDLE

    # Assert：DB 紀錄
    row = fetch_leave(student_id)
    assert row is not None, "應該產生一筆請假紀錄"
    assert row["student_ID"] == student_id
    assert row["reason"] == reason_text
    assert row["context_title"] == context_title

    # Assert：寄信（課程 leave_notice=1）
    assert len(mail_spy.sent) == 1
    assert isinstance(mail_spy.sent[0]["to"], (list, tuple)) and len(
        mail_spy.sent[0]["to"]) >= 1

    # Assert：repo 有被呼叫一次
    assert leave_repo_spy.calls == 1


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_leave_apply_cancel(client, app, container, seed_student_commit, mail_spy, leave_repo_spy, fetch_leave):
    context_title = "1234_程式設計-Python_黃鈺晴教師"
    stu = seed_student_commit(
        context_title=context_title, user_id="U_TEST_USER_ID")
    line_user_id = stu["user_id"]
    student_id = stu["student_id"]

    user_state = container.user_state_accessor()

    # Act：1) 點【請假】
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback("apply_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 2) 取消請假 → 進入 IDLE
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback(
            "[Action]cancel_to_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200
    assert user_state.get_state(
        line_user_id) == UserStateEnum.IDLE

    # Assert：DB 不應有請假紀錄
    row = fetch_leave(student_id)
    assert row is None, "取消請假時不應產生請假紀錄"

    # Assert：不寄信（只有真正寫入請假才會通知）
    assert len(mail_spy.sent) == 0

    # Assert：repo 不應被呼叫
    assert leave_repo_spy.calls == 0


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_check_score_flow(client, app,
                          seed_student_commit, seed_units_commit,
                          line_api_service_spy, score_aggregator_stub, chatbot_logger_spy,
                          monkeypatch):
    """
    Background:
    Given 我已經註冊並登入系統
    And 我開啟了 Pychatbot 主選單

    Scenario: 查詢已開放且存在的單元
    When 我點選「作業繳交查詢」按鈕
    And 我輸入了存在的單元名稱 "C2"
    Then 系統應該查詢該單元成績
    And 系統應該傳送作業的分數給我
    And 系統應該記錄我的查詢事件
    """

    seed_student_commit(context_title="1234_程式設計-Python_黃鈺晴教師")

    seed_units_commit(
        context_title="1234_程式設計-Python_黃鈺晴教師",
        units=[{
            "contents_name": "C1",
            "contents_id": "C1",          # 明確傳也可以
            "context_id": 1234,           # 不傳也會自動從 "1234_..." 推 1234
            "lesson_date": "2025-08-20 10:00:00",
            "publish_flag": 1,
            "oj_d1": 6,
            "summary_d1": 7,
        },
            {
            "contents_name": "C2",
            "contents_id": "C2",          # 明確傳也可以
            "context_id": 1235,           # 不傳也會自動從 "1234_..." 推 1234
            "lesson_date": "2025-08-27 10:00:00",
            "publish_flag": 1,
            "oj_d1": 6,
            "summary_d1": 7,
        }
        ],
        set_deadline=True,
    )

    monkeypatch.setattr(
        CheckScoreService, "_format_score_report",
        lambda self, report: "SCORE MSG",  # 注意要收 self, report
        raising=True,
    )

    line_user_id = "U_TEST_USER_ID"
    unit_name = "C2"

    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback(
            "check_homework", user_id=line_user_id))
    )
    assert resp.status_code == 200

    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_message_text(
            text=unit_name, user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 3) 斷言：a) 回覆內容正確
    assert any("SCORE MSG" in r["text"] for r in line_api_service_spy.replies)

    # 4) 斷言：b) aggregator 有被以正確參數呼叫（至少單元名稱）
    assert any(call["unit_name"] ==
               "C2" for call in score_aggregator_stub.calls), score_aggregator_stub.calls

    # 6) 斷言：d) 有記錄事件
    # 至少有記一次訊息
    assert len(chatbot_logger_spy.messages) >= 1

    last_mid = chatbot_logger_spy.messages[-1]["id"]
    assert any(
        e.get("message_log_id") == last_mid and e.get("hw_id") == "C2"
        for e in chatbot_logger_spy.events
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_check_score_with_no_published_unit(client, app, container,
                                            seed_student_commit, seed_units_commit,
                                            line_api_service_spy, score_aggregator_stub, chatbot_logger_spy,
                                            monkeypatch):
    seed_student_commit(context_title="1234_程式設計-Python_黃鈺晴教師")

    seed_units_commit(
        context_title="1234_程式設計-Python_黃鈺晴教師",
        units=[],              # 沒有任何開放單元
        set_deadline=True,
    )

    monkeypatch.setattr(
        CheckScoreService, "_format_score_report",
        lambda self, report: "SCORE MSG",  # 就算被叫也不影響；但此情境不會用到
        raising=True,
    )

    line_user_id = "U_TEST_USER_ID"

    # 使用者點「作業繳交查詢」
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback("check_homework", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # a) 立即回覆「目前還沒有任何要繳交的作業喔。」
    assert any("目前還沒有任何要繳交的作業" in r["text"]
               for r in line_api_service_spy.replies)

    # b) 狀態應回到 IDLE（不進入 AWAITING_CONTENTS_NAME）
    user_state = container.user_state_accessor()
    assert user_state.get_state(line_user_id) == UserStateEnum.IDLE

    # c) aggregator 不應被呼叫
    assert len(score_aggregator_stub.calls) == 0

    # d) 不應記錄 CHECK_HOMEWORK 事件
    assert not any(e.get("event_type") ==
                   EventEnum.CHECK_HOMEWORK for e in chatbot_logger_spy.events)


@pytest.mark.usefixtures("linebot_mysql_truncate")
@pytest.mark.parametrize("invalid_unit", ["C9", "c2"])
def test_check_score_with_nonexistent_unit(
    client, app, container,
    seed_student_commit, seed_units_commit,
    line_api_service_spy, score_aggregator_stub, chatbot_logger_spy,
    monkeypatch, invalid_unit
):
    seed_student_commit(context_title="1234_程式設計-Python_黃鈺晴教師")

    seed_units_commit(
        context_title="1234_程式設計-Python_黃鈺晴教師",
        units=[
            {
                "contents_name": "C1",
                "contents_id": "C1",
                "context_id": 1234,
                "lesson_date": "2025-08-20 10:00:00",
                "publish_flag": 1,
                "oj_d1": 6,
                "summary_d1": 7,
            },
            {
                "contents_name": "C2",
                "contents_id": "C2",
                "context_id": 1235,
                "lesson_date": "2025-08-27 10:00:00",
                "publish_flag": 1,
                "oj_d1": 6,
                "summary_d1": 7,
            },
        ],
        set_deadline=True,
    )

    # 即使 aggregator 不會被用到，仍 stub 以保持一致
    monkeypatch.setattr(
        CheckScoreService, "_format_score_report",
        lambda self, report: "SCORE MSG",
        raising=True,
    )

    line_user_id = "U_TEST_USER_ID"

    # Step 1: 點「作業繳交查詢」
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback("check_homework", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 應提示輸入單元，並進入等待輸入狀態
    assert any("請輸入要查詢的單元" in r["text"] for r in line_api_service_spy.replies)
    user_state = container.user_state_accessor()
    assert user_state.get_state(
        line_user_id) == UserStateEnum.AWAITING_CONTENTS_NAME

    # Step 2: 輸入不存在的單元名稱
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_message_text(
            text=invalid_unit, user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 斷言：提示不存在、狀態回到 IDLE、沒有聚合與事件
    assert any("單元名稱不存在" in r["text"] for r in line_api_service_spy.replies)
    assert user_state.get_state(line_user_id) == UserStateEnum.IDLE
    assert len(score_aggregator_stub.calls) == 0
    assert not any(e.get("event_type") ==
                   EventEnum.CHECK_HOMEWORK for e in chatbot_logger_spy.events)


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_ask_TA_flow(client, app, container, seed_student_commit, line_api_service_spy, chatbot_logger_spy):
    """
    Scenario: 成功完成提問
    Given 我已經註冊並登入系統
    And 我開啟了 Pychatbot 主選單
    When 我點選「我有問題」按鈕
    And 我留下問題
    Then 系統應該記錄我的提問操作
    """
    seed_student_commit(context_title="1234_程式設計-Python_黃鈺晴教師")

    line_user_id = "U_TEST_USER_ID"
    question_text = "退選"

    user_state = container.user_state_accessor()

    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_message_text(
            text="助教安安，我有問題!", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # 應回提示 + 狀態切到 AWAITING_TA_QUESTION
    assert any("請同學留下問題" in r["text"]
               for r in line_api_service_spy.replies), line_api_service_spy.replies
    assert user_state.get_state(
        line_user_id) == UserStateEnum.AWAITING_TA_QUESTION

    # 2) 第二次訊息：實際把問題丟出（例如 "退選"）

    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_message_text(
            text=question_text, user_id=line_user_id))
    )
    assert resp.status_code == 200

    # submit_question 之後，狀態回到 IDLE
    assert user_state.get_state(line_user_id) == UserStateEnum.IDLE

    # 3) 驗證事件被記錄，且 message_log_id = 第二則訊息的 log_message id
    msg_id_for_question = next(
        m["id"] for m in chatbot_logger_spy.messages
        if m.get("message") == question_text
    )

    assert any(
        e.get("event_type") == EventEnum.ASK_TA_QUESTION
        and e.get("message_log_id") == msg_id_for_question
        for e in chatbot_logger_spy.events
    ), {"messages": chatbot_logger_spy.messages, "events": chatbot_logger_spy.events}


def test_leave_interrupt_then_check_score(client, app, container, seed_student_commit, seed_units_commit):
    """
    在任何一個多步驟的流程中，如果進行了其他操作，應以新操作爲準．
    """
    seed_student_commit(context_title="1234_程式設計-Python_黃鈺晴教師")

    seed_units_commit(
        context_title="1234_程式設計-Python_黃鈺晴教師",
        units=[{
            "contents_name": "C1",
            "contents_id": "C1",          # 明確傳也可以
            "context_id": 1234,           # 不傳也會自動從 "1234_..." 推 1234
            "lesson_date": "2025-08-20 10:00:00",
            "publish_flag": 1,
            "oj_d1": 6,
            "summary_d1": 7,
        }],
        set_deadline=True,
    )
    line_user_id = "U_TEST_USER_ID"

    user_state_accessor = container.user_state_accessor()

    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback("apply_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200

    # Step 2: 確認請假 -> 應進入 AWAITING_LEAVE_REASON 並回覆填寫理由提示
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback(
            "[Action]confirm_to_leave", user_id=line_user_id))
    )
    assert resp.status_code == 200
    assert user_state_accessor.get_state(
        line_user_id) == UserStateEnum.AWAITING_LEAVE_REASON

    # Step 3: 進行其他會切換狀態的操作
    resp, _ = post_line_event(
        client, app,
        make_base_envelope(ev_postback(
            "check_homework", user_id=line_user_id))
    )
    assert resp.status_code == 200
    assert user_state_accessor.get_state(
        line_user_id) == UserStateEnum.AWAITING_CONTENTS_NAME
