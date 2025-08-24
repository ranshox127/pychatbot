# uv run -m pytest tests/interfaces/test_postback_event.py
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from domain.user_state import UserStateEnum
from tests.helpers import make_base_envelope, ev_postback, post_line_event


def _make_student():
    # 簡單學生物件即可（避免依賴 domain class）
    return SimpleNamespace(
        student_id="S0001",
        line_user_id="U_POSTBACK",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        is_registered=lambda: True,
    )


@pytest.mark.parametrize(
    "data,expect_called",
    [
        ("apply_leave", "leave_apply"),
        ("fetch_absence_info", "attendance"),
        ("check_homework", "score_publish"),
        ("[Action]confirm_to_leave", "leave_reason"),
        ("[Action]cancel_to_leave", "cancel_idle"),
    ],
)
def test_postback_triggers_expected_service(client, app, container, data, expect_called):
    # ---- Arrange: common mocks ----
    student = _make_student()

    mock_repo = MagicMock()
    mock_repo.find_by_line_id.return_value = student

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 777  # 給 confirm_to_leave 用

    mock_leave = MagicMock()
    mock_att = MagicMock()
    mock_score = MagicMock()
    mock_state = MagicMock()

    with container.student_repo.override(mock_repo), \
            container.chatbot_logger.override(mock_logger), \
            container.leave_service.override(mock_leave), \
            container.check_attendance_service.override(mock_att), \
            container.check_score_service.override(mock_score), \
            container.user_state_accessor.override(mock_state):

        payload = make_base_envelope(ev_postback(
            data=data, user_id=student.line_user_id))

        # ---- Act ----
        resp, _ = post_line_event(client, app, payload)
        assert resp.status_code == 200

    # ---- Assert: common logging call ----
    mock_logger.log_message.assert_called_once_with(
        student_id=student.student_id, message=data, context_title=student.context_title
    )

    # ---- Assert: branch-specific ----
    if expect_called == "leave_apply":
        mock_leave.apply_for_leave.assert_called_once_with(
            student=student, reply_token="test_reply_token_123"
        )
        mock_att.check_attendance.assert_not_called()
        mock_score.check_publish_contents.assert_not_called()
        mock_leave.ask_leave_reason.assert_not_called()
        mock_state.set_state.assert_not_called()

    elif expect_called == "attendance":
        mock_att.check_attendance.assert_called_once_with(
            student=student, reply_token="test_reply_token_123"
        )
        mock_leave.apply_for_leave.assert_not_called()
        mock_score.check_publish_contents.assert_not_called()
        mock_leave.ask_leave_reason.assert_not_called()
        mock_state.set_state.assert_not_called()

    elif expect_called == "score_publish":
        mock_score.check_publish_contents.assert_called_once_with(
            student=student, reply_token="test_reply_token_123"
        )
        mock_leave.apply_for_leave.assert_not_called()
        mock_att.check_attendance.assert_not_called()
        mock_leave.ask_leave_reason.assert_not_called()
        mock_state.set_state.assert_not_called()

    elif expect_called == "leave_reason":
        mock_leave.ask_leave_reason.assert_called_once_with(
            student=student, reply_token="test_reply_token_123", message_log_id=777
        )
        mock_leave.apply_for_leave.assert_not_called()
        mock_att.check_attendance.assert_not_called()
        mock_score.check_publish_contents.assert_not_called()
        mock_state.set_state.assert_not_called()

    elif expect_called == "cancel_idle":
        mock_state.set_state.assert_called_once_with(
            student.line_user_id, UserStateEnum.IDLE)
        mock_leave.apply_for_leave.assert_not_called()
        mock_att.check_attendance.assert_not_called()
        mock_score.check_publish_contents.assert_not_called()
        mock_leave.ask_leave_reason.assert_not_called()

    else:
        raise AssertionError("Unknown expectation key")
