from typing import Optional

import pymysql

from domain.score import SummaryRepository


class MySQLSummaryRepository(SummaryRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def get_latest_log_id(self, stdID: str, context_title: str, contents_name: str) -> Optional[int]:
        with self._get_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                SELECT log_id
                FROM summary_gradding_log
                WHERE student_ID = %s and context_title = %s and contents_name like %s
                ORDER BY operation_time DESC
                LIMIT 1;
                '''
                cur.execute(query, (stdID, context_title, contents_name,))
                row = cur.fetchone()
                return row["log_id"] if row else None

    def is_log_under_review(self, log_id: int) -> bool:
        with self._get_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                SELECT COUNT(*)
                FROM SummarySubmissions
                WHERE summary_gradding_log_id = %s
                AND verify_status = 'wait_review';
                '''
                cur.execute(query, (log_id,))
                row = cur.fetchone()

                if row['COUNT(*)'] == 1:
                    return True
                return False

    def get_score_result(self, stdID: str, context_title: str,
                         contents_name: str, deadline: str) -> Optional[int]:
        with self._get_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                # 第一層：result = 1 => 100 分
                query_100 = '''
                    SELECT 1
                    FROM summary_gradding_log
                    WHERE result = 1
                    AND context_title = %s
                    AND contents_name LIKE %s
                    AND student_ID = %s
                    AND operation_time <= %s
                    LIMIT 1;
                '''
                cur.execute(query_100, (context_title,
                            contents_name + "%", stdID, deadline))
                if cur.fetchone():
                    return 100

                # 第二層：result = 0 且 penalty != -1 => 80 分
                query_80 = '''
                    SELECT 1
                    FROM summary_gradding_log
                    WHERE result = 0
                    AND penalty != -1
                    AND context_title = %s
                    AND contents_name LIKE %s
                    AND student_ID = %s
                    AND operation_time <= %s
                    LIMIT 1;
                '''
                cur.execute(query_80, (context_title,
                            contents_name + "%", stdID, deadline))
                if cur.fetchone():
                    return 80

                return 0
