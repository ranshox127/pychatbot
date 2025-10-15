# uv run -m pytest tests/application/test_leave_service.py
from unittest.mock import MagicMock

import pytest

from application.leave_service import LeaveService
from domain.student import RoleEnum, Student, StudentStatus
from domain.user_state import UserStateEnum

pytestmark = pytest.mark.unit


@pytest.fixture
def student():
    return Student("lineid", "114514000", "12345", "旅歐文", "1122_程式設計-Python_黃鈺晴教師", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def service():

    course_repo = MagicMock()
    leave_repo = MagicMock()
    user_state = MagicMock()
    line = MagicMock()
    logger = MagicMock()
    mail_carrier = MagicMock()

    return LeaveService(
        course_repo, leave_repo, user_state, line, logger, mail_carrier
    ), course_repo, leave_repo, user_state, line, logger, mail_carrier


def test_apply_for_leave_sends_form(service, student):
    svc, course_repo, *_ = service
    course_repo.get_course_shell.return_value.get_next_course_date.return_value = "2025-07-30"

    svc.apply_for_leave(student, "reply_token")

    course_repo.get_course_shell.assert_called_once_with(student.context_title)
    course_repo.get_course_shell.return_value.get_next_course_date.assert_called_once()
    svc.line_service.reply_message.assert_called_once()


def test_ask_leave_reason_sets_state_and_logs(service, student):
    svc, _, _, _, _, logger, _ = service

    svc.ask_leave_reason(student, "token", 42)

    logger.log_event.assert_called_once()
    svc.user_state_accessor.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.AWAITING_LEAVE_REASON)
    svc.line_service.reply_text_message.assert_called_once()


def test_submit_leave_reason_sends_email_if_needed(service, student):
    svc, course_repo, _, _, _, _, mailer = service

    course_repo.get_course_shell.return_value.get_next_course_date.return_value = "2025-07-30"
    course_repo.get_course_shell.return_value.leave_notice = True
    course_repo.get_course_shell.return_value.ta_emails = ["ta@school.edu"]
    svc.leave_repo.save_leave_request.return_value = "收到，已經幫你請好假了。"

    svc.submit_leave_reason(student, "感冒", "reply_token")

    mailer.send_email.assert_called_once()


def test_submit_leave_reason_does_not_send_email_if_flag_false(service, student):
    svc, course_repo, *_ = service
    course_repo.get_course_shell.return_value.leave_notice = False
    svc.leave_repo.save_leave_request.return_value = "收到，已經幫你請好假了。"

    svc.submit_leave_reason(student, "感冒", "reply_token")

    svc.mail_carrier.send_email.assert_not_called()


def test_now_string_format():
    svc = LeaveService(None, None, None, None, None, None)
    result = svc._now_string()
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)
