# application/chatbot_logger.py
from datetime import datetime

from domain.event_log import EventEnum, EventLog
from domain.message_log import MessageLog


class ChatbotLogger:
    def __init__(self, message_repo, event_repo):
        self.message_repo = message_repo
        self.event_repo = event_repo

    def log_message(self, student_id: str, message: str, context_title: str = None) -> int:
        msg_log = MessageLog(
            operation_time=datetime.now(),
            student_id=student_id,
            message=message,
            context_title=context_title
        )
        return self.message_repo.save_message_log(msg_log)

    def log_event(self, student_id: str, event_type: EventEnum, message_log_id: int = None,
                  problem_id=None, hw_id=None, context_title=None):
        event_log = EventLog(
            operation_time=datetime.now(),
            student_id=student_id,
            event_type=event_type,
            message_log_id=message_log_id,
            problem_id=problem_id,
            hw_id=hw_id,
            context_title=context_title
        )
        self.event_repo.save_event_log(event_log)
