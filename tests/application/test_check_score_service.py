# uv run -m pytest tests/application/test_check_score_service.py
import pytest
from unittest.mock import MagicMock

from application.check_score_service import CheckScoreService
from domain.student import Student, StudentStatus, RoleEnum
from domain.course import Course, CourseUnit
from domain.user_state import UserStateEnum
from domain.score import ScoreReport


@pytest.fixture
def student():
    return Student("lineid", "114514000", "12345", "旅歐文", "1122_程式設計-Python_黃鈺晴教師", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def course_with_units():
    unit = CourseUnit("C4")
    course = Course("1122_程式設計-Python_黃鈺晴教師",
                    ["mail"], 1, 3, "contest", "sheet", [unit])
    return course


@pytest.fixture
def course_empty():
    return Course("1122_程式設計-Python_黃鈺晴教師", ["mail"], 1, 3, "contest", "sheet", [])


@pytest.fixture
def service():

    course_repo = MagicMock()
    user_state = MagicMock()
    aggregator = MagicMock()
    line = MagicMock()
    logger = MagicMock()

    return CheckScoreService(
        course_repo, user_state, aggregator, line, logger
    ), course_repo, user_state, aggregator, line, logger


def test_check_publish_contents_has_no_contents(service, student, course_empty):
    """
    Scenario: 尚未有任何開放的單元

    Expect:
    系統應該通知「目前還沒有任何要繳交的作業喔。」
    學生的狀態應重置成 IDLE
    """

    svc, course_repo, user_state, aggregator, line, logger = service

    course_repo.get_course_shell.return_value = course_empty
    course_repo.populate_units.return_value = course_empty

    svc.check_publish_contents(student, "reply_token")

    line.reply_text_message.assert_called_once_with(
        reply_token="reply_token",
        text="目前還沒有任何要繳交的作業喔。"
    )
    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.IDLE)


def test_check_publish_contents_has_contents():
    """
    Scenario: 存在已開放的單元

    Expect:
    系統應該通知「請輸入要查詢的單元。(ex. {unit_list_text})」
    學生的狀態應轉換成 AWAITING_CONTENTS_NAME
    """


def test_check_score_with_wrong_content():
    """
    Scenario: 查詢不存在的單元

    Expect:
    系統應該通知「請單元名稱不存在，請確認後再重新查詢喔。」
    學生的狀態應重置成 IDLE
    """


def test_check_score_with_right_content():
    """
    Scenario: 查詢已開放且存在的單元

    Expect:
    系統應該通知對應的章節的各項活動的分數(看當時什麼狀況)
    學生的狀態應重置成 IDLE
    系統應該記錄該次的 event
    """
