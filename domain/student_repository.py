# domain/student_repository.py (介面定義也可以放在 domain 層)
from abc import ABC, abstractmethod
from typing import Optional
from student import Student

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