# infrastructure/mysql_feedback_push_repository.py

import pymysql
from domain.summary_repositories import FeedbackPushRepository


class MySQLFeedbackPushRepository(FeedbackPushRepository):
    def __init__(self, linebot_db_config: dict):
        self.linebot_db_config = linebot_db_config

    def _get_linebot_db_connection(self):
        return pymysql.connect(**self.linebot_db_config)

    def check_summary_feedback_push(self, stdID: str, context_title: str, contents_name: str) -> bool:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                SELECT *
                FROM summary_feedback_push
                WHERE student_ID = %s
                AND context_title = %s
                AND contents_name = %s
                """
                cur.execute(query, (stdID, context_title, contents_name,))

                return cur.fetchone() is None

    def write_summary_feedback_push(self, stdID: str, context_title: str, contents_name: str) -> None:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                INSERT INTO summary_feedback_push (created_at, context_title, contents_name, student_id)
                VALUES (
                    CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '+08:00'),
                    %s, %s, %s
                )
                """
                cur.execute(query, (context_title, contents_name, stdID))
            conn.commit()
