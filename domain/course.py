from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from enum import Enum
from datetime import date, timedelta


@dataclass
class DeadlinesVO:  # Value Object
    oj_d1: str
    summary_d1: str


@dataclass
class CourseUnit:  # Entity (within Course Aggregate)
    name: str
    deadlines: DeadlinesVO

    def get_homework_deadlines(self, base_date: date) -> dict:
        return {
            "oj": (base_date + timedelta(days=self.deadlines.oj_d1)).strftime("%Y-%m-%d 04:01:00"),
            "summary": (base_date + timedelta(days=self.deadlines.summary_d1)).strftime("%Y-%m-%d 12:01:00")
        }


class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4


@dataclass
class Course:  # Aggregate Root
    context_title: str
    ta_emails: List[str]
    leave_notice: int
    day_of_week: int
    oj_contest_title: str
    attendance_sheet_url: str
    units: List[CourseUnit]

    def get_next_course_date(self) -> str:
        today = date.today()
        today_weekday = today.weekday()  # 0 = Monday
        days_until_next = (self.day_of_week - today_weekday) % 7
        days_until_next = days_until_next or 7  # same day => next week
        next_date = today + timedelta(days=days_until_next)
        return str(next_date)


class CourseRepository(ABC):
    @abstractmethod
    def get_in_progress_courses(self, reserved: str = "") -> list[Course]:
        pass

    @abstractmethod
    def get_course_shell(self, context_title: str) -> Course:
        """
        回傳 context_title, ta_emails, leave_notice, day_of_week, oj_contest_title, attendance_sheet_url
        """
        pass

    @abstractmethod
    def populate_units(self, course: Course) -> Course:
        pass
