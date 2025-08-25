# uv run -m pytest tests/interfaces/test_operation_flow.py
# uv run -m pytest tests/interfaces/test_operation_flow.py::test_leave_full_flow -s
from types import SimpleNamespace
import pytest

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


# def test_check_score_flow(client, app, container):
#     """
#     Background:
#     Given 我已經註冊並登入系統
#     And 我開啟了 Pychatbot 主選單

#     Scenario: 查詢已開放且存在的單元
#     When 我點選「作業繳交查詢」按鈕
#     And 我輸入了存在的單元名稱 "C4"
#     Then 系統應該查詢該單元成績
#     And 系統應該傳送作業的分數給我
#     And 系統應該記錄我的查詢事件
#     """


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
