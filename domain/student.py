# domain/student.py
from dataclasses import dataclass
from enum import Enum, auto


class StudentStatus(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()


@dataclass
class Student:
    """我們的核心領域物件：學生聚合根"""
    line_user_id: str
    student_id: str
    moodle_id: str
    name: str
    course_title: str
    role_id: int
    status: StudentStatus

    @staticmethod
    def register(line_user_id: str, student_id: str, moodle_id: str, name: str, course_title: str, role_id: int) -> 'Student':
        """
        工廠方法：用於建立一個新的、已註冊的學生實例。
        這裡可以放入與建立學生相關的業務規則。
        """
        # 可以在這裡加驗證，例如 student_id 或 name 不可為空
        if not student_id or not line_user_id:
            raise ValueError("Student ID and Line User ID cannot be empty.")

        return Student(
            line_user_id=line_user_id,
            student_id=student_id,
            moodle_id=moodle_id,
            name=name,
            course_title=course_title,
            role_id=role_id,
            status=StudentStatus.REGISTERED
        )

    def is_registered(self) -> bool:
        return self.status == StudentStatus.REGISTERED
