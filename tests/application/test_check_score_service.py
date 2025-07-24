# uv run -m pytest tests/application/test_check_score_service.py
from unittest.mock import MagicMock

import pytest

from application.check_score_service import CheckScoreService
from domain.course import Course, CourseUnit
from domain.event_log import EventEnum
from domain.score import ScoreReport
from domain.student import RoleEnum, Student, StudentStatus
from domain.user_state import UserStateEnum


@pytest.fixture
def student():
    return Student("lineid", "114514000", "12345", "旅歐文", "1122_程式設計-Python_黃鈺晴教師", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def course_with_units():
    unit_1 = CourseUnit("C1")
    unit_2 = CourseUnit("C2")
    course = Course("1122_程式設計-Python_黃鈺晴教師",
                    ["mail"], 1, 3, "contest", "sheet", [unit_1, unit_2])
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


def test_check_publish_contents_has_contents(service, student, course_with_units):
    """
    Scenario: 存在已開放的單元

    Expect:
    系統應該通知「請輸入要查詢的單元。(ex. {unit_list_text})」
    學生的狀態應轉換成 AWAITING_CONTENTS_NAME
    """

    svc, course_repo, user_state, aggregator, line, logger = service

    course_repo.get_course_shell.return_value = course_with_units
    course_repo.populate_units.return_value = course_with_units

    svc.check_publish_contents(student, "reply_token")

    line.reply_text_message.assert_called_once_with(
        reply_token="reply_token",
        text="請輸入要查詢的單元。(ex. C1, C2)"
    )

    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.AWAITING_CONTENTS_NAME)


def test_check_score_with_wrong_content(service, student, course_with_units):
    """
    Scenario: 查詢不存在的單元

    Expect:
    系統應該通知「請單元名稱不存在，請確認後再重新查詢喔。」
    學生的狀態應重置成 IDLE
    """

    svc, course_repo, user_state, aggregator, line, logger = service

    course_repo.get_course_shell.return_value = course_with_units
    course_repo.populate_units.return_value = course_with_units

    wrong_content = " C1"

    svc.check_score(student, "reply_token", wrong_content, "url", "001")

    line.reply_text_message.assert_called_once_with(
        reply_token="reply_token",
        text="單元名稱不存在，請確認後再重新查詢喔。"
    )

    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.IDLE)


def test_check_score_with_right_content(service, student, course_with_units):
    """
    Scenario: 查詢已開放且存在的單元

    Expect:
    系統應該通知對應的章節的各項活動的分數(看當時什麼狀況)
    學生的狀態應重置成 IDLE
    系統應該記錄該次的 event
    """

    svc, course_repo, user_state, aggregator, line, logger = service

    course_repo.get_course_shell.return_value = course_with_units
    course_repo.populate_units.return_value = course_with_units

    right_content = "C1"

    # Arrange: 模擬分數報告
    aggregator.aggregate.return_value = ScoreReport(
        contents_name="C1",
        scores={
            "OJ Exercise(完成題數)": "9 / 10",
            "OJ Advance(完成題數)": "4 / 5",
            "總結概念成績": "100",
            "錯誤回顧成績": "100"
        }
    )

    svc.check_score(student, "reply_token", right_content, "url", 42)

    # Assert: 檢查文字格式正確
    sent_msg = line.reply_text_message.call_args.kwargs["text"]
    assert "C1 作業成績" in sent_msg
    for key in aggregator.aggregate.return_value.scores.keys():
        assert key in sent_msg

    # Assert: 狀態應轉為 IDLE
    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.IDLE)

    # Assert: 有記錄 event log
    logger.log_event.assert_called_once_with(
        student_id=student.student_id,
        event_type=EventEnum.CHECK_HOMEWORK,
        message_log_id=42,
        problem_id=None,
        hw_id="C1",
        context_title=student.context_title
    )
