from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class EventEnum(Enum):
    REGISTER = "register"
    CHECK_PRESENT = "check_present"
    CHECK_HOMEWORK = "check_homework"
    ASK_FOR_LEAVE = "ask_for_leave"
    ASK_TA_QUESTION = "Ask_TA_question"
    CODING_HELP = "coding_help"

    GET_SUMMARY_GRADING = "get_summary_grading"
    SUMMARY_REGRADING = "summary_re-gradding"
    CHALLENGE_SUMMARY_GRADING = "challenge_summary_gradding"
    GET_SUMMARY_MENU = "get_summary_menu"

    GAI_SOLVE_COMPLETE = "GAI_solve_complete"
    GAI_SOLVE_PARTIAL = "GAI_solve_partial"
    GAI_SOLVE_NONE = "GAI_solve_none"
    ASK_GAI_AUTO_REPLY = "ask_GAI_auto_reply"


@dataclass
class EventLog:
    operation_time: datetime
    student_id: str
    event_type: EventEnum
    problem_id: Optional[str] = None
    hw_id: Optional[str] = None
    context_title: Optional[str] = None
    message_log_id: Optional[int] = None
    gai_auto_reply_status: Optional[int] = None  # 0, 1, 2 for GAI reply
    log_id: Optional[int] = None  # 放最後，不要預設


class EventLogRepository(ABC):

    @abstractmethod
    def save_event_log(self, event_log: EventLog) -> None:
        pass
