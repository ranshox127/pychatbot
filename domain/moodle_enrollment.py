from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MoodleEnrollment:
    """一個清晰的資料傳輸物件(DTO)，代表一個學生的註冊資訊"""
    course_fullname: str
    roleid: int
    user_id: str  # Moodle user ID
    fullname: str  # Student's full name


class MoodleRepository(ABC):
    @abstractmethod
    def find_student_info(self, student_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def find_student_enrollments(self, student_id: str) -> List[MoodleEnrollment]:
        pass
