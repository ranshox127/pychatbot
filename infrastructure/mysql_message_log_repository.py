# infrastructure/mysql_message_log_repository.py
import pymysql
from domain.message_log import MessageLog, MessageLogRepository


class MySQLMessageLogRepository(MessageLogRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def save_message_log(self, message_log: MessageLog) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO message_logs (operation_time, student_ID, message, context_title)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    message_log.operation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    message_log.student_id,
                    message_log.message,
                    message_log.context_title
                ))
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()
