# application/ports/grading_port.py
from typing import Protocol


class GradingPort(Protocol):
    def grade_single(self, student_id: str, context_title: str,
                     contents_name: str) -> dict: ...
    # 回傳至少包含 {"status": "...", "log_id": int|None}
