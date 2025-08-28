from types import SimpleNamespace


class FakeMoodleRepo:
    """最小可行的 Moodle stub，符合 RegistrationService 會用到的兩個方法。"""

    def __init__(self, *, student_id: str, fullname: str, course_fullname: str, roleid: int = 5, user_id: int = 999):
        self._student_id = student_id
        self._fullname = fullname
        self._course_fullname = course_fullname
        self._roleid = roleid
        self._user_id = user_id

    def find_student_info(self, student_id: str):
        # 回傳類似 Enrollment 的東西，只要屬性名字對得上就行
        if student_id == self._student_id:
            return SimpleNamespace(
                user_id=self._user_id,
                fullname=self._fullname,
                course_fullname=self._course_fullname,
                roleid=self._roleid,
            )
        return None

    def find_student_enrollments(self, student_id: str):
        # 回傳多門課也行；至少包含你在 MySQL 中 seed 的那一門
        if student_id != self._student_id:
            return []
        return [
            SimpleNamespace(
                user_id=self._user_id,
                fullname=self._fullname,
                course_fullname=self._course_fullname,
                roleid=self._roleid,
            )
        ]
