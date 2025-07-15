# infrastructure/mysql_event_log_repository.py
import pymysql

from domain.event_log import EventLog, EventLogRepository


class MySQLEventLogRepository(EventLogRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def save_event_log(self, event_log: EventLog) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO event_logs (
                        operation_time, student_ID, operation_event,
                        problem_id, HW_id, context_title, message_log_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    event_log.operation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    event_log.student_id,
                    event_log.event_type.value,
                    event_log.problem_id,
                    event_log.hw_id,
                    event_log.context_title,
                    event_log.message_log_id
                ))
                conn.commit()
        finally:
            conn.close()
