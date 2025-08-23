# uv run -m pytest tests/interfaces/test_postback_event.py
from unittest.mock import MagicMock, ANY
from types import SimpleNamespace
from tests.helpers import make_base_envelope, ev_postback, post_line_event


def test_postback_apply_leave(client, app, container):
    # 純 mock 版本（不寫 DB），展示如何覆寫 service 和 repo
    fake_student = SimpleNamespace(
        student_id="S12345678", line_user_id="U_TEST_USER_ID", context_title="idle")

    mock_leave_service = MagicMock()
    mock_student_repo = MagicMock()
    mock_student_repo.find_by_line_id.return_value = fake_student
    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 123

    with container.leave_service.override(lambda: mock_leave_service), \
            container.student_repo.override(lambda: mock_student_repo), \
            container.chatbot_logger.override(lambda: mock_logger):

        payload = make_base_envelope(ev_postback(
            "apply_leave", user_id="U_TEST_USER_ID"))
        resp, _ = post_line_event(client, app, payload)

    assert resp.status_code == 200
    mock_student_repo.find_by_line_id.assert_called_once_with("U_TEST_USER_ID")
    mock_leave_service.apply_for_leave.assert_called_once_with(
        student=ANY, reply_token="test_reply_token_123")
