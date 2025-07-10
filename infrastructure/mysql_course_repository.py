import pymysql

from domain.course import Course, CourseRepository


class MySQLCourseRepository(CourseRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def get_in_progress_courses(self, reserved: str = "") -> list[Course]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                SELECT context_title
                FROM course_info
                WHERE status = 'in_progress' AND reserved LIKE %s;
                """
                cur.execute(query, (reserved,))
                row = cur.fetchone()
                return [self._map_row_to_course(row)] if row else []

    def get_course_info(self, context_title: str) -> Course:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM course_info WHERE context_title = %s;"
                cur.execute(query, (context_title,))
                row = cur.fetchone()
                return self._map_row_to_course(row) if row else None

    def _map_row_to_course(self, row: dict) -> Course:
        return Course(
            context_title=row["context_title"],
            ta_emails=row["mails_of_TAs"].split(
                ",") if row["mails_of_TAs"] else [],
            oj_contest_title=row["OJ_contest_title"],
            attendance_sheet_url=row["present_url"],
            units=[]
        )
