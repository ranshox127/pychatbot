import pymysql

from domain.feedback import FeedbackRepository


class MySQLFeedbackRepository(FeedbackRepository):
    def __init__(self, verify_db_config: dict):
        self.verify_db_config = verify_db_config

    def _get_verify_db_connection(self):
        return pymysql.connect(**self.verify_db_config)

    def get_summarysubmissions(self):
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                sql = '''
                SELECT SubmissionId, StudentId, context_title, TopicId, student_summary, SubmitTime, verify_status, basic_feedback, GPT_Feedback, summary_gradding_log_id, LineID
                FROM SummarySubmissions
                WHERE verify_status = 'wait_review'
                '''
                cur.execute(sql)
                rows = cur.fetchall()
                return rows

    def complete_review_summarysubmission(self, submission_id):
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                sql = '''
                UPDATE SummarySubmissions
                SET verify_status = %s
                WHERE SubmissionId = %s
                '''
                cur.execute(sql, ('complete_review', submission_id))
            conn.commit()

    def insert_teacher_feedback(
            self, SubmissionId, SubmissionType, Feedback, FeedbackTime, context_title, LineID):
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                sql = '''
                INSERT INTO TeacherFeedbacks (SubmissionId, SubmissionType, Feedback, FeedbackTime, context_title, LineID)
                VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.execute(sql, (SubmissionId, SubmissionType,
                            Feedback, FeedbackTime, context_title, LineID))
                feedback_id = cur.lastrowid
            conn.commit()
            return feedback_id

    def insert_summary_feedback_evaluation(
            self, FeedbackId, Accuracy, Readability, Clarity, Consistency, Answerability):
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                sql = '''
                INSERT INTO FeedbackEvaluations_v1 (FeedbackId, Accuracy, Readability, Clarity, Consistency, Answerability)
                VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.execute(sql, (FeedbackId, Accuracy, Readability,
                            Clarity, Consistency, Answerability))
                evaluation_id = cur.lastrowid
            conn.commit()
            return evaluation_id
