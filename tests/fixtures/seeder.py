# 不依賴 pytest，任何地方都能 import 後帶 conn 來用
from __future__ import annotations
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Sequence, Union


def seed_course(conn, *,
                context_title="1122_程式設計-Python_黃鈺晴教師",
                status="in_progress",
                present_url="https://docs.google.com/spreadsheets/d/123456/edit#gid=0",
                mails_of_TAs="ta@example.com",
                leave_notice=1,
                day_of_week=2,
                OJ_contest_title="中央_1122",
                reserved="",
                ) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO course_info
              (`context_title`, `status`, `present_url`, `mails_of_TAs`, 
                `leave_notice`, `day_of_week`, `OJ_contest_title`, `reserved`)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              status=VALUES(status),
              present_url=VALUES(present_url),
              mails_of_TAs=VALUES(mails_of_TAs),
              leave_notice=VALUES(leave_notice),
              day_of_week=VALUES(day_of_week),
              OJ_contest_title=VALUES(OJ_contest_title),
              reserved=VALUES(reserved)
            """,
            (context_title, status, present_url, mails_of_TAs,
             leave_notice, day_of_week, OJ_contest_title, reserved),
        )
    return {"context_title": context_title}


def seed_student(conn, *,
                 student_id="S12345678",
                 user_id="U_TEST_USER_ID",
                 mdl_id="12345",
                 name="旅歐文",
                 context_title="1122_程式設計-Python_黃鈺晴教師",
                 roleid=5,
                 deleted=0,
                 ) -> Dict[str, Any]:
    seed_course(conn, context_title=context_title)  # 先確保課程存在
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO account_info
                (student_ID, line_userID, mdl_ID, student_name, context_title, roleid, `del`)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              line_userID=VALUES(line_userID),
              mdl_ID=VALUES(mdl_ID),
              student_name=VALUES(student_name),
              context_title=VALUES(context_title),
              roleid=VALUES(roleid),
              `del`=VALUES(`del`)
            """,
            (student_id, user_id, mdl_id, name, context_title, roleid, deleted),
        )
    return {
        "student_id": student_id, "user_id": user_id, "mdl_id": mdl_id,
        "name": name, "context_title": context_title,
    }


def seed_change_deadline(conn, *, context_title, contents_name, oj_d1=6, summary_d1=7):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO change_HW_deadline (context_title, contents_name, OJ_D1, Summary_D1)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              OJ_D1=VALUES(OJ_D1),
              Summary_D1=VALUES(Summary_D1)
            """,
            (context_title, contents_name, oj_d1, summary_d1),
        )


def seed_summary_grading_log(conn, *,
                             student_ID, context_title, contents_name,
                             result=1, penalty=0, operation_time="2025-08-01 10:00:00",
                             ):
    # linebot DB: summary_gradding_log
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO summary_gradding_log (student_ID, context_title, contents_name, result, penalty, operation_time)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (student_ID, context_title, contents_name,
             result, penalty, operation_time),
        )


def seed_review_publish(conn, *,
                        context_title, contents_name, lesson_date="2025-08-01 10:00:00",
                        publish_flag=1, context_id=None, contents_id=None,
                        ):
    if context_id is None:
        # 從 context_title 前綴推 context_id，如 1122_...
        try:
            context_id = int(context_title.split("_", 1)[0])
        except Exception:
            context_id = 1
    if contents_id is None:
        contents_id = contents_name
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO review_publish
              (context_title, context_id, contents_name, contents_id, lesson_date, publish_flag)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (context_title, context_id, contents_name,
             contents_id, lesson_date, publish_flag),
        )


def seed_summary_submission(conn, *, summary_gradding_log_id, student_id=None, topic_id=None, gpt_feedback=None,
                            submit_time=None, verify_status="wait_review", context_title=None, student_summary=None,
                            basic_feedback=None, line_id=None):
    # 設置當前時間為預設提交時間，如果未提供 submit_time
    submit_time = submit_time or datetime.now()

    # 若沒有提供其他欄位的值，則設定為 None（或可以根據需要設定其他預設值）
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO SummarySubmissions (
                summary_gradding_log_id, StudentId, TopicId, GPT_Feedback, SubmitTime, verify_status, context_title,
                student_summary, basic_feedback, LineID
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                summary_gradding_log_id, student_id, topic_id, gpt_feedback, submit_time, verify_status, context_title,
                student_summary, basic_feedback, line_id
            )
        )


def seed_units(
    review_conn,                        # review-system 的 MySQL 連線
    linebot_conn,                       # linebot 的 MySQL 連線
    *,
    context_title: str = "1122_程式設計-Python_黃鈺晴教師",
    units: Optional[Sequence[Dict[str, Any]]] = None,
    set_deadline: bool = True,
    default_oj_d1: int = 6,
    default_summary_d1: int = 7,
    default_lesson_date: str = "2025-08-20 10:00:00",   # 固定值，避免 CI 不穩
) -> Dict[str, Any]:
    """
    在 review_publish 寫入單元；必要時在 change_HW_deadline 寫入 D1 期限。
    units 每筆格式：
      {
        "contents_name": "C1_變數概念" 或 "C1",
        "lesson_date": "2025-08-20 10:00:00" 或 datetime,  # 選填
        "publish_flag": 1,                                 # 選填，預設 1
        "context_id": 1234,                                # 選填，預設由 context_title 推斷
        "contents_id": "C1",                               # 選填，預設 = contents_name
        "oj_d1": 6, "summary_d1": 7                        # 只有在 set_deadline=True 時會用到
      }
    """

    def _infer_context_id(context_title: str, fallback: int = 1) -> int:
        m = re.match(r"^(\d+)_", context_title or "")
        return int(m.group(1)) if m else fallback

    def _to_ts(v: Union[str, datetime], default_ts: str) -> str:
        if v is None:
            return default_ts
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return str(v)

    inferred_ctx_id = _infer_context_id(context_title)

    # 1) review_publish（review-system DB）
    with review_conn.cursor() as cur:
        for u in units:
            contents_name = u["contents_name"]
            lesson_date = _to_ts(u.get("lesson_date"), default_lesson_date)
            publish_flag = u.get("publish_flag", 1)
            context_id = u.get("context_id", inferred_ctx_id)
            contents_id = u.get("contents_id", contents_name)

            # 注意：review_publish 通常沒有唯一鍵，因此用單純 INSERT
            cur.execute(
                """
                INSERT INTO review_publish
                  (context_title, context_id, contents_name, contents_id, lesson_date, publish_flag)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (context_title, context_id, contents_name,
                 contents_id, lesson_date, publish_flag),
            )

    # 2) change_HW_deadline（linebot DB）
    if set_deadline:
        with linebot_conn.cursor() as cur2:
            for u in units:
                contents_name = u["contents_name"]
                oj_d1 = u.get("oj_d1", default_oj_d1)
                summary_d1 = u.get("summary_d1", default_summary_d1)
                cur2.execute(
                    """
                    INSERT INTO change_HW_deadline
                      (context_title, contents_name, OJ_D1, Summary_D1)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      OJ_D1 = VALUES(OJ_D1),
                      Summary_D1 = VALUES(Summary_D1)
                    """,
                    (context_title, contents_name, oj_d1, summary_d1),
                )

    # 回傳 normalized 結構
    normalized: List[Dict[str, Any]] = []
    for u in units:
        ld = _to_ts(u.get("lesson_date"), default_lesson_date)
        normalized.append({
            "contents_name": u["contents_name"],
            "contents_id": u.get("contents_id", u["contents_name"]),
            "lesson_date": ld,
            "publish_flag": u.get("publish_flag", 1),
            "context_id": u.get("context_id", inferred_ctx_id),
            "oj_d1": u.get("oj_d1", default_oj_d1),
            "summary_d1": u.get("summary_d1", default_summary_d1),
        })
    return {"context_title": context_title, "units": normalized}


def seed_leave(conn, *, operation_time, student_ID, student_name, apply_time, reason, context_title):
    # 確保相關學生資料存在，這裡依賴已經實作好的 `seed_student`
    seed_student(conn, student_id=student_ID, context_title=context_title)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ask_for_leave (operation_time, student_ID, student_name, apply_time, reason, context_title)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                reason=VALUES(reason)
            """,
            (operation_time, student_ID, student_name,
             apply_time, reason, context_title)
        )
    conn.commit()
    return {
        "student_ID": student_ID, "apply_time": apply_time, "context_title": context_title
    }
