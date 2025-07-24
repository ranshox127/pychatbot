# uv run -m pytest tests/application/test_ask_TA_service.py
from unittest.mock import MagicMock

import pytest

from application.ask_TA_service import AskTAService
from domain.event_log import EventEnum
from domain.student import RoleEnum, Student, StudentStatus
from domain.user_state import UserStateEnum


@pytest.fixture
def student():
    return Student("lineid", "114514000", "12345", "旅歐文", "1122_程式設計-Python_黃鈺晴教師", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def service():

    user_state = MagicMock()
    line = MagicMock()
    logger = MagicMock()

    return AskTAService(user_state, line, logger), user_state, line, logger


def test_start_inquiry_behavior(student, service):
    """
    Scenario: 按下按鈕

    Expect:
    學生的狀態應轉換成 AWAITING_TA_QUESTION
    系統應該通知「請同學留下問題~助教會盡快回覆!」
    """

    svc, user_state, line, logger = service

    svc.start_inquiry(student, "reply_token")

    line.reply_text_message.assert_called_once_with(
        reply_token="reply_token",
        text="請同學留下問題~助教會盡快回覆!"
    )
    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.AWAITING_TA_QUESTION)


def test_submit_question_behavior(student, service):
    """
    Scenario: 成功完成提問

    Expect:
    學生的狀態應重置成 IDLE
    系統應該記錄該次的 event
    """

    svc, user_state, line, logger = service

    svc.submit_question(student, 42)

    user_state.set_state.assert_called_once_with(
        student.line_user_id, UserStateEnum.IDLE)

    logger.log_event.assert_called_once_with(
        student_id=student.student_id,
        event_type=EventEnum.ASK_TA_QUESTION,
        message_log_id=42,
        problem_id=None,
        hw_id=None,
        context_title=student.context_title
    )
