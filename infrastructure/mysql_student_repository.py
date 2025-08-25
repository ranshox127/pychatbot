# infrastructure/mysql_student_repository.py
from enum import Enum
from typing import Optional

import pymysql

from domain.student import RoleEnum, Student, StudentStatus, StudentRepository


class MySQLStudentRepository(StudentRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config, cursorclass=pymysql.cursors.DictCursor)

    def find_by_line_id(self, line_user_id: str) -> Optional[Student]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 使用參數化查詢，防止 SQL 注入
                sql = """
                SELECT ai.* FROM account_info ai
                JOIN course_info ci ON ai.context_title = ci.context_title
                WHERE ai.line_userID = %s AND ai.del = 0
                AND ci.status = 'in_progress' AND ci.reserved LIKE "";
                """
                cur.execute(sql, (line_user_id,))
                row = cur.fetchone()
                return self._map_row_to_student(row) if row else None

    def find_by_student_id(self, student_id: str) -> Optional[Student]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 使用參數化查詢，防止 SQL 注入
                sql = """
                SELECT ai.* FROM account_info ai
                JOIN course_info ci ON ai.context_title = ci.context_title
                WHERE ai.student_ID = %s AND ai.del = 0
                AND ci.status = 'in_progress' AND ci.reserved LIKE "";
                """
                cur.execute(sql, (student_id,))
                row = cur.fetchone()
                return self._map_row_to_student(row) if row else None

    def save(self, student: Student) -> None:
        def _to_roleid(val) -> int:
            if isinstance(val, Enum):
                return int(val.value)
            return int(val)
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
                    student.student_id, student.line_user_id, student.mdl_id,
                    student.name, student.context_title, _to_roleid(student.role)
                ))
            conn.commit()

    def _map_row_to_student(self, row: dict) -> Student:
        return Student(
            line_user_id=row['line_userID'],
            student_id=row['student_ID'],
            mdl_id=row['mdl_ID'],
            name=row['student_name'],
            context_title=row['context_title'],
            role=RoleEnum(row['roleid']),
            is_active=(row['del'] == 0),
            status=StudentStatus.REGISTERED
        )
