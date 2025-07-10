# infrastructure/postgresql_moodle_repository.py
from typing import List, Optional

import psycopg2
from sshtunnel import SSHTunnelForwarder

from domain.moodle_enrollment import MoodleEnrollment, MoodleRepository


class PostgreSQLMoodleRepository(MoodleRepository):
    def __init__(self, db_config: dict, ssh_config: dict):
        self.db_config = db_config
        self.ssh_config = ssh_config

    def _get_connection(self):
        tunnel = SSHTunnelForwarder(
            (self.ssh_config['host'], self.ssh_config.get('port', 22)),
            ssh_username=self.ssh_config['username'],
            ssh_password=self.ssh_config['password'],
            remote_bind_address=(
                self.db_config['host'], self.db_config['port'])
        )
        tunnel.start()

        conn = psycopg2.connect(
            host='127.0.0.1',
            port=tunnel.local_bind_port,
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
        return tunnel, conn

    def find_student_enrollments(self, student_id: str) -> List[MoodleEnrollment]:
        tunnel, conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # 這個 SQL 不再需要 course.fullname 作為 WHERE 條件
                sql = """
                SELECT
                    cour.fullname,
                    ra.roleid,
                    usr.id,
                    CONCAT(usr.lastname, usr.firstname)
                FROM mdl_user AS usr
                JOIN mdl_role_assignments AS ra ON ra.userid = usr.id
                JOIN mdl_context AS context ON context.id = ra.contextid
                JOIN mdl_course AS cour ON cour.id = context.instanceid
                WHERE (usr.username = %s OR usr.username LIKE %s);
                """
                cur.execute(sql, (student_id, student_id + '@%'))
                rows = cur.fetchall()
                # 將查詢結果映射到我們定義的 DTO 列表
                return [MoodleEnrollment(course_fullname=row[0], roleid=row[1], user_id=row[2], fullname=row[3]) for row in rows]
        finally:
            conn.close()
            tunnel.close()

    def find_student_info(self, course_fullname: str, student_id: str) -> Optional[dict]:
        """
        根據 Moodle 課程名稱與學生帳號（可能為 username 或 username@開頭）查找該學生資訊。
        """
        tunnel, conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = """
                SELECT DISTINCT usr.id AS user_id,
                       usr.username,
                       CONCAT(usr.lastname, usr.firstname) AS fullname,
                       ra.roleid
                FROM mdl_course AS cour
                JOIN mdl_enrol AS enrol ON cour.id = enrol.courseid
                JOIN mdl_user_enrolments AS ue ON enrol.id = ue.enrolid
                JOIN mdl_user AS usr ON ue.userid = usr.id
                JOIN mdl_role_assignments AS ra ON ra.userid = usr.id
                JOIN mdl_context AS context ON context.id = ra.contextid AND context.instanceid = cour.id
                WHERE cour.fullname = %s
                  AND (usr.username = %s OR usr.username LIKE %s)
                ORDER BY ra.roleid
                LIMIT 1;
                """
                cur.execute(
                    sql, (course_fullname, student_id, student_id + '@%'))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "user_id": row[0],
                    "student_id": row[1].split('@')[0],
                    "fullname": row[2],
                    "roleid": row[3]
                }
        finally:
            conn.close()
            tunnel.close()
