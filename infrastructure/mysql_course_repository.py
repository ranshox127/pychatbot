# infrastructure/mysql_course_repository.py
from datetime import datetime

import pymysql

from domain.course import Course, CourseRepository, CourseUnit


class MySQLCourseRepository(CourseRepository):
    def __init__(self, linebot_db_config: dict, rs_db_config: dict):
        self.linebot_db_config = linebot_db_config
        self.rs_db_config = rs_db_config

    def _get_linebot_db_connection(self):
        return pymysql.connect(**self.linebot_db_config)

    def _get_rs_db_connection(self):
        return pymysql.connect(**self.rs_db_config)

    def get_in_progress_courses(self, reserved: str = "") -> list[Course]:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = """
                SELECT context_title, mails_of_TAs, leave_notice, day_of_week, OJ_contest_title, present_url
                FROM course_info
                WHERE status = 'in_progress' AND reserved LIKE %s;
                """
                cur.execute(query, (reserved,))
                rows = cur.fetchall()
                return [self._map_row_to_course(row) for row in rows] if rows else []

    def get_course_shell(self, context_title: str) -> Course:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = "SELECT * FROM course_info WHERE context_title = %s;"
                cur.execute(query, (context_title,))
                row = cur.fetchone()
                return self._map_row_to_course(row) if row else None

    def populate_units(self, course: Course) -> Course:
        with self._get_rs_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                    SELECT contents_name, start_time
                    FROM review_system.review_publish
                    WHERE context_title = %s
                    AND publish_flag = 1;
                '''
                cur.execute(query, (course.context_title,))
                rows = cur.fetchall()

                units = []
                for row in rows:
                    contents_name = row['contents_name']
                    unit_name = contents_name.split('_')[0]
                    start_time = row['start_time']  # "%Y-%m-%d %H:%M:%S"

                    # 查詢自訂 deadline（天數）
                    query_dl = '''
                        SELECT OJ_D1, Summary_D1
                        FROM review_system.change_homework_deadline
                        WHERE context_title = %s AND contents_name = %s
                    '''
                    cur.execute(
                        query_dl, (course.context_title, contents_name))
                    dl_row = cur.fetchone()

                    # 決定延後幾天
                    oj_days = dl_row['OJ_D1'] if dl_row else 6
                    summary_days = dl_row['Summary_D1'] if dl_row else 7

                    base_date = start_time.date() if isinstance(
                        start_time, datetime) else datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date()

                    unit = CourseUnit(name=unit_name)

                    unit.get_homework_deadlines(
                        base_date=base_date, oj_d1=oj_days, summary_d1=summary_days)

                    units.append(unit)

                course.units = units

        return course

    def _map_row_to_course(self, row: dict) -> Course:
        return Course(
            context_title=row["context_title"],
            ta_emails=row["mails_of_TAs"].split(
                ",") if row["mails_of_TAs"] else [],
            leave_notice=row["leave_notice"],
            day_of_week=row["day_of_week"],
            oj_contest_title=row["OJ_contest_title"],
            attendance_sheet_url=row["present_url"],
            units=[]
        )
