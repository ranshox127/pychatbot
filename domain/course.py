# domain/course.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
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

    def get_next_course_date(self, start_hour: int = 9) -> str:
        """
        實際的課程起始時間請詢問 Anna，以取得正確的 start_hour。
        沒有考量到颱風假、國定假日、Anna 的行程，它就只是計算下週上課日期。
        
        注意: `date.today()` 回傳系統當下的日期，所以不要亂搞電腦。
        """
        today = date.today()
        now = datetime.now()
        today_weekday = today.weekday()

        days_until_next = (self.day_of_week - today_weekday) % 7

        # 處理同一天邏輯
        if days_until_next == 0:
            if now.hour < start_hour:
                next_date = today
            else:
                next_date = today + timedelta(days=7)
        else:
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
