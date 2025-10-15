# uv run -m pytest tests/application/test_chatbot_logger.py
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from application.chatbot_logger import ChatbotLogger
from domain.event_log import EventEnum, EventLog
from domain.message_log import MessageLog

pytestmark = pytest.mark.unit


def test_log_message_should_call_repo_with_correct_data():
    message_repo = MagicMock()
    event_repo = MagicMock()
    logger = ChatbotLogger(message_repo, event_repo)

    message_repo.save_message_log.return_value = 42

    result = logger.log_message("S123", "這是一則訊息", "Python 課程")

    # 檢查回傳的 ID
    assert result == 42

    # 檢查傳入的 MessageLog 結構
    saved_msg: MessageLog = message_repo.save_message_log.call_args[0][0]
    assert saved_msg.student_id == "S123"
    assert saved_msg.message == "這是一則訊息"
    assert saved_msg.context_title == "Python 課程"
    assert saved_msg.log_id is None
    assert isinstance(saved_msg.operation_time, datetime)


def test_log_event_should_call_repo_with_correct_data():
    message_repo = MagicMock()
    event_repo = MagicMock()
    logger = ChatbotLogger(message_repo, event_repo)

    logger.log_event(
        student_id="S123",
        event_type=EventEnum.ASK_TA_QUESTION,
        message_log_id=99,
        problem_id="p001",
        hw_id="C3",
        context_title="Python 課程"
    )

    saved_event: EventLog = event_repo.save_event_log.call_args[0][0]
    assert saved_event.student_id == "S123"
    assert saved_event.event_type == EventEnum.ASK_TA_QUESTION
    assert saved_event.message_log_id == 99
    assert saved_event.problem_id == "p001"
    assert saved_event.hw_id == "C3"
    assert saved_event.context_title == "Python 課程"
    assert saved_event.log_id is None
    assert isinstance(saved_event.operation_time, datetime)
