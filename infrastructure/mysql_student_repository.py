# infrastructure/mysql_student_repository.py
import pymysql
from domain.student import Student, StudentStatus
from domain.student_repository import StudentRepository
from typing import Optional


class MySQLStudentRepository(StudentRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def find_by_line_id(self, line_user_id: str) -> Optional[Student]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 使用參數化查詢，防止 SQL 注入
                sql = "SELECT * FROM account_info WHERE line_userID = %s AND del = 0"
                cur.execute(sql, (line_user_id,))
                row = cur.fetchone()
                return self._map_row_to_student(row) if row else None

    def find_by_student_id(self, student_id: str) -> Optional[Student]:
        # ... 類似的實作 ...
        pass

    def save(self, student: Student) -> None:
        sql = """
            INSERT INTO account_info (student_ID, line_userID, mdl_ID, student_name, context_title, roleid, del)
            VALUES (%s, %s, %s, %s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE 
                mdl_ID = VALUES(mdl_ID), 
                student_name = VALUES(student_name),
                context_title = VALUES(context_title),
                roleid = VALUES(roleid),
                del = 0;
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    student.student_id, student.line_user_id, student.moodle_id,
                    student.name, student.course_title, student.role_id
                ))
            conn.commit()

    def _map_row_to_student(self, row: dict) -> Student:
        return Student(
            line_user_id=row['line_userID'],
            student_id=row['student_ID'],
            moodle_id=row['mdl_ID'],
            name=row['student_name'],
            course_title=row['context_title'],
            role_id=row['roleid'],
            status=StudentStatus.REGISTERED
        )
