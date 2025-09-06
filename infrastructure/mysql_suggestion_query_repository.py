# infrastructure/mysql_suggestion_query_repository.py
import ast
import json
from typing import Any, Dict, List, Optional, Tuple

import pymysql
from domain.summary_repositories import SuggestionQueryRepository


class MySQLSuggestionQueryRepository(SuggestionQueryRepository):
    def __init__(self, linebot_db_config: dict, verify_db_config: dict):
        self.linebot_db_config = linebot_db_config
        self.verify_db_config = verify_db_config

    def _get_linebot_db_connection(self):
        return pymysql.connect(**self.linebot_db_config)

    def _get_verify_db_connection(self):
        return pymysql.connect(**self.verify_db_config)

    def is_log_under_review(self, log_id: int) -> bool:
        with self._get_verify_db_connection() as conn:
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

    def get_questions(self, context_title: str, contents_name: str) -> Tuple[List[str], List[str]]:
        """
        依 context_title / contents_name 取得 (keywords, questions)。
        回傳兩個等長的 list，索引對應同一筆資料。
        """
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                    SELECT keyword, question
                    FROM concept_keyword_and_question
                    WHERE context_title = %s
                    AND contents_name = %s
                    AND `del` = 0
                '''

                cur.execute(query, (context_title, contents_name+'_'))
                rows = cur.fetchall() or []

                kws: List[str] = [row["keyword"]
                                  for row in rows if row.get("keyword") is not None]
                questions: List[str] = [row["question"]
                                        for row in rows if row.get("question") is not None]
                return kws, questions

    def get_example_summary(self, context_title: str, contents_name: str) -> Optional[str]:
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                    SELECT summary
                    FROM concept_summary_example
                    WHERE context_title = %s
                    AND contents_name = %s
                '''
                cur.execute(query, (context_title, contents_name+'_'))
                result = cur.fetchone()
                return result['summary'] if result and 'summary' in result else None

    def check_summary_in_SummarySubmissions(self, log_id: int) -> bool:
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                SELECT COUNT(*) AS cnt
                FROM SummarySubmissions
                WHERE summary_gradding_log_id = %s
                '''
                cur.execute(query, (log_id,))
                row = cur.fetchone()
                # row 例：{'cnt': 0 or >0}
                return bool(row and row.get('cnt', 0) > 0)

    def use_summary_grading_log_id_get_GenAI_feedback(self, log_id: int) -> Optional[str]:
        with self._get_verify_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                query = '''
                SELECT tf.Feedback
                FROM SummarySubmissions ss
                JOIN TeacherFeedbacks tf ON ss.SubmissionId = tf.SubmissionId
                WHERE ss.summary_gradding_log_id = %s
                AND tf.SubmissionType = 'Summary'
                ORDER BY tf.FeedbackTime DESC
                LIMIT 1;
                '''

                cur.execute(query, (log_id,))
                result = cur.fetchone()
                return result['Feedback'] if result and 'Feedback' in result else None

    def get_suggestion_info(
        self,
        student_id: str,
        context_title: str,
        contents_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        取回最近一筆 summary_gradding_log 與對應的 lime_explain_log。
        回傳格式：
        {
          'log_id': int,
          'summary': str,
          'loss_kw': List[str],
          'similarity': float | None,
          'penalty': float | None,
          'score': int | None,
          'result': int | None,
          'excess': List[str],
          'loss_concept_kws': List[str],
        }
        若查無資料回傳 None。
        """
        with self._get_linebot_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                # 先抓最近一筆 grading log
                cur.execute(
                    """
                    SELECT log_id, summary, loss_kw, similarity, penalty, score, result
                    FROM summary_gradding_log
                    WHERE context_title = %s
                      AND contents_name = %s
                      AND student_ID   = %s
                    ORDER BY log_id DESC
                    LIMIT 1
                    """,
                    (context_title, contents_name, student_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                out: Dict[str, Any] = {
                    "log_id": int(row["log_id"]),
                    "summary": row.get("summary") or "",
                    "loss_kw": self._parse_list_field(row.get("loss_kw")),
                    "similarity": float(row["similarity"]) if row.get("similarity") is not None else None,
                    "penalty": float(row["penalty"]) if row.get("penalty") is not None else None,
                    "score": int(row["score"]) if row.get("score") is not None else None,
                    "result": int(row["result"]) if row.get("result") is not None else None,
                }

                # 再抓對應的 lime_explain_log（若有多筆，拿最新）
                cur.execute(
                    """
                    SELECT excess, loss_concept_kws
                    FROM lime_explain_log
                    WHERE summary_gradding_log_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (out["log_id"],),
                )
                lime = cur.fetchone()
                if lime:
                    out["excess"] = self._parse_list_field(lime.get("excess"))
                    out["loss_concept_kws"] = self._parse_list_field(
                        lime.get("loss_concept_kws"))
                else:
                    out["excess"] = []
                    out["loss_concept_kws"] = []

                return out

    @staticmethod
    def _parse_list_field(val: Any) -> List[str]:
        """
        安全解析 DB 內以文字形式存的 list：
        1) 優先當 JSON 解析
        2) 失敗改用 ast.literal_eval
        3) 再失敗就用逗號切
        """
        if val is None:
            return []
        s = val if isinstance(val, str) else str(val)

        # try JSON first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass

        # then safe literal_eval
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass

        # fallback: comma-separated
        return [part.strip() for part in s.split(",") if part.strip()]
