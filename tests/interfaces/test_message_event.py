# uv run -m pytest tests/interfaces/test_message_event.py
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from domain.user_state import UserStateEnum
from tests.helpers import make_base_envelope, ev_message_text, post_line_event


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_register_flow(client, app, container, seed_course_commit):
    # 未註冊（收到訊息 -> 當作註冊學號）

    seed_course_commit(context_title="1122_程式設計-Python_黃鈺晴教師")

    # 建立 mocks
    mock_registration = MagicMock()
    mock_student_repo = MagicMock()
    mock_student_repo.find_by_line_id.return_value = None  # 查無此人 → 會走註冊流程

    with container.registration_service.override(mock_registration), \
            container.student_repo.override(mock_student_repo):

        payload = make_base_envelope(
            ev_message_text(text="114514005", user_id="U_NEW")
        )

        # 送進 webhook
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    # 驗證：確實呼叫了註冊服務
    mock_registration.register_student.assert_called_once_with(
        "U_NEW", "114514005", "test_reply_token_123"  # 我們 helper 的預設 replyToken
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_leave_reason_flows_to_leave_service(client, app, container):
    # 已註冊學生（回一個簡單物件即可）
    student = SimpleNamespace(
        student_id="S12345678",
        line_user_id="U1",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,  # 讓第二層檢查 pass
    )

    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 321

    mock_state = MagicMock()
    mock_state.get_state.return_value = SimpleNamespace(
        status=UserStateEnum.AWAITING_LEAVE_REASON)

    mock_leave = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.user_state_accessor.override(mock_state), \
            container.leave_service.override(mock_leave):

        payload = make_base_envelope(
            ev_message_text(text="感冒請假", user_id="U1"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    mock_leave.submit_leave_reason.assert_called_once_with(
        student=student, reason="感冒請假", reply_token="test_reply_token_123"
    )
    # 可補充：logger 有沒有被叫
    mock_logger.log_message.assert_called_once_with(
        student_id="S12345678", message="感冒請假", context_title="1122_程式設計-Python_黃鈺晴教師"
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_ta_question_flows_to_ask_ta(client, app, container):
    student = SimpleNamespace(
        student_id="S12345678",
        line_user_id="U2",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,
    )
    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 987

    mock_state = MagicMock()
    mock_state.get_state.return_value = SimpleNamespace(
        status=UserStateEnum.AWAITING_TA_QUESTION)

    mock_ask_ta = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.user_state_accessor.override(mock_state), \
            container.ask_ta_service.override(mock_ask_ta):

        payload = make_base_envelope(
            ev_message_text(text="請問作業2提示？", user_id="U2"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    mock_ask_ta.submit_question.assert_called_once_with(
        student=student, message_log_id=987
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_awaiting_contents_name_flows_to_check_score(client, app, container):
    student = SimpleNamespace(
        student_id="S0001",
        line_user_id="U3",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,
    )
    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 555

    mock_state = MagicMock()
    mock_state.get_state.return_value = SimpleNamespace(
        status=UserStateEnum.AWAITING_CONTENTS_NAME)

    mock_score = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.user_state_accessor.override(mock_state), \
            container.check_score_service.override(mock_score):

        payload = make_base_envelope(
            ev_message_text(text="C3", user_id="U3"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    mock_score.check_score.assert_called_once_with(
        student=student,
        reply_token="test_reply_token_123",
        target_content="C3",
        message_log_id=555,
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_idle_and_command_triggers_start_inquiry(client, app, container):
    # 已註冊 + IDLE + 指令「助教安安，我有問題!」→ 啟動詢問流程
    student = SimpleNamespace(
        student_id="S0002",
        line_user_id="U4",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,
    )
    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 42

    mock_state = MagicMock()
    mock_state.get_state.return_value = SimpleNamespace(
        status=UserStateEnum.IDLE)

    mock_ask_ta = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.user_state_accessor.override(mock_state), \
            container.ask_ta_service.override(mock_ask_ta):

        payload = make_base_envelope(
            ev_message_text(text="助教安安，我有問題!", user_id="U4"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    mock_ask_ta.start_inquiry.assert_called_once_with(
        student=student, reply_token="test_reply_token_123"
    )


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_message_idle_default_text(client, app, container):
    # 一般文字
    student = SimpleNamespace(
        student_id="S0002",
        line_user_id="U4",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,
    )
    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 42

    mock_state = MagicMock()
    mock_state.get_state.return_value = SimpleNamespace(
        status=UserStateEnum.IDLE)

    mock_ask_ta = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.user_state_accessor.override(mock_state), \
            container.ask_ta_service.override(mock_ask_ta):

        payload = make_base_envelope(
            ev_message_text(text="測試", user_id="U4"))
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    mock_ask_ta.start_inquiry.assert_not_called()
