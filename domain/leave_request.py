from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LeaveRequest:
    operation_time: str
    student_id: str
    student_name: str
    apply_time: str
    reason: str
    context_title: str


class LeaveRequestRepository(ABC):
    @abstractmethod
    def save_leave_request(self, leave: LeaveRequest) -> str:
        pass
