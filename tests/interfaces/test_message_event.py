# uv run -m pytest tests/interfaces/test_message_event.py
from types import SimpleNamespace
import pytest
from domain.user_state import UserStateEnum
from tests.helpers import make_base_envelope, ev_message_text, client_post_event, wait_for


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_register_flow(client, app, it_seed_course, student_repo_stub, service_spies):
    # 未註冊（收到訊息 -> 當作註冊學號）

    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'

    # it_seed_course(context_title=course_title)

    # 學生查無此人 → 會走註冊流程
    student_repo_stub.set_find_by_line_id(line_id, None)

    payload = make_base_envelope(
        ev_message_text(text=student_id, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    # 驗證：確實呼叫了註冊服務
    reg_spy = service_spies["registration"]
    assert reg_spy.called(
        "register_student"), "預期呼叫 registration.register_student，但沒有"
    call = reg_spy.last_call("register_student")
    # 我們 helper 的預設 replyToken
    assert call.args == (line_id, student_id, "test_reply_token_123")


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_leave_reason_flows_to_leave_service(client, app,
                                                              it_seed_student, student_repo_stub, chatbot_logger_spy,
                                                              user_state_spy, service_spies):

    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'j'
    reason = "感冒請假"

    student = SimpleNamespace(
        student_id=student_id,
        line_user_id=line_id,
        context_title=course_title,
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    it_seed_student(user_id=line_id,
                    student_id=student_id,
                    name=name,
                    context_title=course_title,)

    student_repo_stub.set_find_by_line_id(line_id, student)

    user_state_spy.set_user_state(line_id, UserStateEnum.AWAITING_LEAVE_REASON)

    payload = make_base_envelope(ev_message_text(text=reason, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    ok = wait_for(lambda: service_spies["leave"].called(
        "submit_leave_reason"), timeout=2.0)
    assert ok, f"預期 submit_leave_reason，但沒看到；calls={service_spies['leave'].calls}"

    call = service_spies["leave"].last_call("submit_leave_reason")
    assert call.kwargs == {
        "student": student,
        "reason": reason,
        "reply_token": "test_reply_token_123",
    }

    assert any(m.get("message") ==
               reason for m in chatbot_logger_spy.messages), chatbot_logger_spy.messages


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_ta_question_flows_to_ask_ta(client, app,
                                                      it_seed_student, student_repo_stub, chatbot_logger_spy,
                                                      user_state_spy, service_spies):
    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'j'
    text = "請問作業2提示？"

    student = SimpleNamespace(
        student_id=student_id,
        line_user_id=line_id,
        context_title=course_title,
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    it_seed_student(user_id=line_id,
                    student_id=student_id,
                    name=name,
                    context_title=course_title,)

    student_repo_stub.set_find_by_line_id(line_id, student)

    user_state_spy.set_user_state(line_id, UserStateEnum.AWAITING_TA_QUESTION)

    payload = make_base_envelope(ev_message_text(text=text, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    ok = wait_for(lambda: service_spies["ask_ta"].called(
        "submit_question"), timeout=2.0)
    assert ok, f"預期 submit_question，但沒看到；calls={service_spies['ask_ta'].calls}"

    call = service_spies["ask_ta"].last_call("submit_question")
    assert call.kwargs == {
        "student": student,
        "message_log_id": 1
    }


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_contents_name_flows_to_check_score(client, app, container,
                                                             it_seed_student, student_repo_stub, user_state_spy,
                                                             chatbot_logger_spy, service_spies):
    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'j'
    text = "C3"

    student = SimpleNamespace(
        student_id=student_id,
        line_user_id=line_id,
        context_title=course_title,
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    it_seed_student(user_id=line_id,
                    student_id=student_id,
                    name=name,
                    context_title=course_title,)

    student_repo_stub.set_find_by_line_id(line_id, student)

    user_state_spy.set_user_state(
        line_id, UserStateEnum.AWAITING_CONTENTS_NAME)

    payload = make_base_envelope(ev_message_text(text=text, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    ok = wait_for(lambda: service_spies["score"].called(
        "check_score"), timeout=2.0)
    assert ok, f"預期 check_score，但沒看到；calls={service_spies['score'].calls}"

    call = service_spies["score"].last_call("check_score")
    assert call.kwargs == {
        "student": student,
        "reply_token": "test_reply_token_123",
        "target_content": text,
        "mistake_review_sheet_url": container.config.MISTAKE_REVIEW_SHEET_URL(),
        "message_log_id": 1
    }


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_idle_and_command_triggers_start_inquiry(client, app,
                                                         it_seed_student, student_repo_stub, user_state_spy,
                                                         chatbot_logger_spy, service_spies):
    # 已註冊 + IDLE + 指令「助教安安，我有問題!」→ 啟動詢問流程
    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'j'
    text = "助教安安，我有問題!"

    student = SimpleNamespace(
        student_id=student_id,
        line_user_id=line_id,
        context_title=course_title,
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    it_seed_student(user_id=line_id,
                    student_id=student_id,
                    name=name,
                    context_title=course_title,)

    student_repo_stub.set_find_by_line_id(line_id, student)

    user_state_spy.set_user_state(line_id, UserStateEnum.IDLE)

    payload = make_base_envelope(ev_message_text(text=text, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    ok = wait_for(lambda: service_spies["ask_ta"].called(
        "start_inquiry"), timeout=2.0)
    assert ok, f"預期 start_inquiry，但沒看到；calls={service_spies['ask_ta'].calls}"

    call = service_spies["ask_ta"].last_call("start_inquiry")
    assert call.kwargs == {
        "student": student,
        "reply_token": "test_reply_token_123"
    }


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_idle_default_text(client, app,
                                   it_seed_student, student_repo_stub, user_state_spy,
                                   chatbot_logger_spy, service_spies):
    # 一般文字
    course_title = "1122_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'j'
    text = "d"

    student = SimpleNamespace(
        student_id=student_id,
        line_user_id=line_id,
        context_title=course_title,
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    it_seed_student(user_id=line_id,
                    student_id=student_id,
                    name=name,
                    context_title=course_title,)

    student_repo_stub.set_find_by_line_id(line_id, student)

    user_state_spy.set_user_state(line_id, UserStateEnum.IDLE)
    payload = make_base_envelope(ev_message_text(text=text, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    ask_ta_spy = service_spies["ask_ta"]
    ask_ta_spy.assert_not_called()
