from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MessageLog:
    operation_time: datetime
    student_id: str
    message: str
    context_title: Optional[str] = None
    log_id: Optional[int] = None


class MessageLogRepository(ABC):

    @abstractmethod
    def save_message_log(self, message_log: MessageLog) -> None:
        pass
