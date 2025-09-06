# uv run -m pytest tests/application/test_registration_service.py

from unittest.mock import MagicMock

import pytest

from application.registration_service import RegistrationService
from domain.student import Student, RoleEnum, StudentStatus
from domain.moodle_enrollment import MoodleEnrollment


@pytest.fixture
def student_repo(): return MagicMock()


@pytest.fixture
def course_repo(): return MagicMock()


@pytest.fixture
def moodle_repo(): return MagicMock()


@pytest.fixture
def state_repo(): return MagicMock()


@pytest.fixture
def line_service(): return MagicMock()


@pytest.fixture
def logger(): return MagicMock()


@pytest.fixture
def service(student_repo, course_repo, moodle_repo, state_repo, line_service, logger):
    return RegistrationService(
        student_repo, course_repo, moodle_repo, state_repo, line_service, logger
    )


def test_handle_follow_event_registered(service, student_repo, line_service):
    """
    如果學生已經註冊了，他重新加好友或解除封鎖應該要切到主要菜單
    """
    student_repo.find_by_line_id.return_value = Student(
        "lineid", "sid", "mdl_id", "旅歐文", "課程", RoleEnum.STUDENT, True, StudentStatus.REGISTERED
    )
    service.handle_follow_event("lineid", "reply_token")
    line_service.link_rich_menu_to_user.assert_called_once_with(
        "lineid", "main")


def test_handle_follow_event_unregistered(service, student_repo, line_service):
    """
    如果學生還沒註冊，提醒他輸入學號
    """
    student_repo.find_by_line_id.return_value = None
    service.handle_follow_event("lineid", "reply_token")
    line_service.reply_text_message.assert_called_once()
    assert "請輸入學號" in line_service.reply_text_message.call_args[0][1]


def test_register_student_already_bound(service, student_repo, line_service):
    """
    1. 有其他人不小心佔用學號
    2. 輸入到其他人學號
    """
    student_repo.find_by_student_id.return_value = MagicMock()
    service.register_student("lineid", "114514", "reply_token")
    line_service.reply_text_message.assert_called_once()
    assert "已被其他" in line_service.reply_text_message.call_args[0][1]


def test_register_student_invalid_id(service, student_repo, moodle_repo, line_service):
    """
    1. 自己打錯
    2. moodle 有問題
    """
    student_repo.find_by_student_id.return_value = None
    moodle_repo.find_student_info.return_value = None
    service.register_student("lineid", "114514", "reply_token")
    line_service.reply_text_message.assert_called_once()
    assert "找不到這個學號" in line_service.reply_text_message.call_args[0][1]


def test_register_student_course_not_available(service, student_repo, moodle_repo, course_repo, line_service):
    """
    實際上應該不太會有這情況
    """
    student_repo.find_by_student_id.return_value = None
    moodle_repo.find_student_info.return_value = MagicMock()
    moodle_repo.find_student_enrollments.return_value = [
        MoodleEnrollment("其他課程", 5, "sid", "旅歐文")]
    course_repo.get_in_progress_courses.return_value = []
    service.register_student("lineid", "114514", "reply_token")
    line_service.reply_text_message.assert_called_once()
    assert "未啟用" in line_service.reply_text_message.call_args[0][1]


def test_register_student_success(service, student_repo, moodle_repo, course_repo, state_repo, line_service, logger):
    student_repo.find_by_student_id.return_value = None
    moodle_repo.find_student_info.return_value = MoodleEnrollment(
        "1122_課程", 5, "mdl123", "旅歐文")
    moodle_repo.find_student_enrollments.return_value = [
        MoodleEnrollment("1122_課程", 5, "mdl123", "旅歐文")
    ]
    course_repo.get_in_progress_courses.return_value = [
        MagicMock(context_title="1122_課程")
    ]

    service.register_student("lineid", "114514", "reply_token")

    student_repo.save.assert_called_once()
    state_repo.save.assert_called_once()
    logger.log_event.assert_called_once()
    line_service.link_rich_menu_to_user.assert_called_once_with(
        "lineid", "main")
    line_service.reply_text_message.assert_called()
    msg = line_service.reply_text_message.call_args[0][1]
    assert "很高興認識你" in msg and "1122_課程" in msg
