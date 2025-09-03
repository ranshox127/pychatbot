# infrastructure/mysql_grading_log_repository.py
import datetime
from typing import Optional
import pymysql
from domain.summary_repositories import GradingLogRepository


class MySQLGradingLogRepository(GradingLogRepository):
    def __init__(self, linebot_db_config: dict, verify_db_config: dict):
        self.linebot_db_config = linebot_db_config
        self.verify_db_config = verify_db_config

    def _get_linebot_db_connection(self):
        return pymysql.connect(**self.linebot_db_config)

    def _get_verify_db_connection(self):
        return pymysql.connect(**self.verify_db_config)

    def get_latest_log_id(self, stdID: str, context_title: str, contents_name: str) -> Optional[int]:
        with self._get_linebot_db_connection() as conn:
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

    def get_summary_gradding_times(self, stdID: str, context_title: str, contents_name: str) -> int:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                SELECT count(*) as times
                FROM summary_gradding_log
                WHERE student_ID   = %s
                AND context_title = %s
                AND contents_name = %s
                '''
                cur.execute(query, (stdID, context_title, contents_name,))
                row = cur.fetchone()

                return int(row['times']) if row and row.get('times') is not None else 0

    def write_summary_GPT_feedback_to_verify_db_with_check_repeat(self, StudentId, TopicId, GPT_Feedback, context_title, student_summary, summary_gradding_log_id, basic_feedback, line_id):
        """寫入GenAI生成的summary feedback"""
        submit_time = self.get_timestamp()  # 拿到提交時間
        insert_query = '''
        INSERT INTO SummarySubmissions 
        (StudentId, TopicId, GPT_Feedback, SubmitTime,verify_status, context_title, student_summary, summary_gradding_log_id, basic_feedback, LineID) 
        VALUES (%s, %s, %s, %s, 'wait_review', %s, %s, %s, %s, %s);
        '''
        values = (StudentId, TopicId, GPT_Feedback, submit_time, context_title,
                  student_summary, summary_gradding_log_id, basic_feedback, line_id)

        try:
            with self._get_verify_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 插入資料
                    cursor.execute(insert_query, values)
                    conn.commit()

                    # 查詢新插入的 SubmissionId
                    select_query = '''
                    SELECT SubmissionId FROM SummarySubmissions
                    WHERE StudentId = %s AND SubmitTime = %s;
                    '''
                    cursor.execute(select_query, (StudentId, submit_time))
                    result = cursor.fetchone()

                    if result:
                        submission_id = result['SubmissionId']

                        # 更新其他符合條件的紀錄
                        update_query = '''
                        UPDATE SummarySubmissions
                        SET verify_status = 'covered'
                        WHERE StudentId = %s
                        AND context_title = %s
                        AND TopicId = %s
                        AND verify_status = 'wait_review'
                        AND SubmissionId != %s;
                        '''
                        cursor.execute(
                            update_query, (StudentId, context_title, TopicId, submission_id))
                        conn.commit()

                        return f"已儲存至SummarySubmissions，並更新了 {cursor.rowcount} 筆紀錄的狀態。"
                    else:
                        return "儲存至SummarySubmissions時發生錯誤：無法找到提交記錄。"
        except pymysql.MySQLError as e:
            print(f"Error executing database operations: {e}")
            return f"儲存並更新至SummarySubmissions時發生錯誤: {e}"

    def get_timestamp(self):
        return (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
