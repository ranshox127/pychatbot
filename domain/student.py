# domain/student.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class RoleEnum(Enum):
    TEACHER = 3
    TA = 4
    STUDENT = 5


class StudentStatus(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()


@dataclass
class Student:
    """我們的核心領域物件：學生聚合根"""
    line_user_id: str
    student_id: str
    mdl_id: str
    name: str
    context_title: str
    role: RoleEnum
    is_active: bool  # 取代 del 欄位，意義更清晰
    status: StudentStatus

    @staticmethod
    def register(line_user_id: str, student_id: str, mdl_id: str, name: str, context_title: str, role: RoleEnum, is_active: bool) -> 'Student':
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
            mdl_id=mdl_id,
            name=name,
            context_title=context_title,
            role=role,
            is_active=is_active,
            status=StudentStatus.REGISTERED
        )

    def is_registered(self) -> bool:
        return self.status == StudentStatus.REGISTERED


class StudentRepository(ABC):
    @abstractmethod
    def find_by_line_id(self, line_user_id: str) -> Optional[Student]:
        pass

    @abstractmethod
    def find_by_student_id(self, student_id: str) -> Optional[Student]:
        pass

    @abstractmethod
    def save(self, student: Student) -> None:
        pass
