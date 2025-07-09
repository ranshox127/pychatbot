from dataclasses import dataclass


@dataclass
class LeaveRequest:
    context_title: str
    student_id: str
    leave_date: str
    reason: str
    request_time: str
