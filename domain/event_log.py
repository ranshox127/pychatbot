from dataclasses import dataclass
from enum import Enum


class EventEnum(Enum):
    pass


@dataclass
class EventLog:
    log_id: str
    student_id: str
    event_type: EventEnum
    operation_time: str
    related_id: str
