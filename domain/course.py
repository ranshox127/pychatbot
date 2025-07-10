from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class DeadlinesVO:  # Value Object
    oj_d1: int
    summary_d1: int
    # ... 其他 deadline 欄位


@dataclass
class CourseUnit:  # Entity (within Course Aggregate)
    name: str
    deadlines: DeadlinesVO


@dataclass
class Course:  # Aggregate Root
    context_title: str
    ta_emails: List[str]
    oj_contest_title: str
    attendance_sheet_url: str
    units: List[CourseUnit]


class CourseRepository(ABC):
    @abstractmethod
    def get_in_progress_courses(self, reserved: str = "") -> list[Course]:
        pass

    @abstractmethod
    def get_course_info(self, context_title: str) -> Course:
        pass
