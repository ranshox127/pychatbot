# tests/fixtures/seed_commit.py
from datetime import datetime, timedelta
import re
import pytest


def _infer_context_id(context_title: str, fallback: int = 1) -> int:
    m = re.match(r"^(\d+)_", context_title or "")
    return int(m.group(1)) if m else fallback


@pytest.fixture
def seed_units_commit(rs_mysql_truncate, linebot_mysql_truncate):
    """
    整合測試：在 review-system DB 的 review_publish 插入單元，
    並（可選）在 linebot DB 的 change_HW_deadline 插入對應 D1 期限。

    Args:
        context_title (str)
        units (list[dict] | None): 每筆格式：
            {
              "contents_name": "C1_變數概念" 或 "C1",
              "lesson_date": "2025-08-20 10:00:00" 或 datetime,
              "publish_flag": 1,        # 預設 1
              "context_id": 1234,       # 預設從 context_title 推斷
              "contents_id": "C1"       # 預設等於 contents_name
              "oj_d1": 6,               # 非 review DB 欄位，用於 change_HW_deadline
              "summary_d1": 7           # 非 review DB 欄位，用於 change_HW_deadline
            }
        set_deadline (bool): 是否寫入 change_HW_deadline，預設 True
        default_oj_d1 (int): 預設 6
        default_summary_d1 (int): 預設 7
    Returns:
        {"context_title": str, "units": [ ...normalized... ]}
    """
    def _seed_units(
        *,
        context_title="1122_程式設計-Python_黃鈺晴教師",
        units=None,
        set_deadline=True,
        default_oj_d1=6,
        default_summary_d1=7,
    ):
        if units is None:
            # 預設一筆，時間往後 1 小時
            dt = datetime.now() + timedelta(hours=1)
            units = [{
                "contents_name": "C1_單元一",
                "lesson_date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "publish_flag": 1,
            }]

        inferred_ctx_id = _infer_context_id(context_title)

        # --- 1) review_publish（review-system DB）--------------------------------
        with rs_mysql_truncate.cursor() as cur:
            for u in units:
                contents_name = u["contents_name"]
                lesson_date = u.get("lesson_date", datetime.now())
                if isinstance(lesson_date, datetime):
                    lesson_date = lesson_date.strftime("%Y-%m-%d %H:%M:%S")
                publish_flag = u.get("publish_flag", 1)

                context_id = u.get("context_id", inferred_ctx_id)
                contents_id = u.get("contents_id", contents_name)

                # 注意：review_publish 沒有唯一鍵，ON DUPLICATE KEY 不會觸發；用單純 INSERT 即可
                cur.execute(
                    """
                    INSERT INTO review_publish
                        (context_title, context_id, contents_name, contents_id, lesson_date, publish_flag)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (context_title, context_id, contents_name,
                     contents_id, lesson_date, publish_flag),
                )

        # --- 2) change_HW_deadline（linebot DB）----------------------------------
        if set_deadline:
            with linebot_mysql_truncate.cursor() as cur2:
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
        normalized = []
        for u in units:
            ld = u.get("lesson_date")
            if isinstance(ld, datetime):
                ld = ld.strftime("%Y-%m-%d %H:%M:%S")
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

    return _seed_units
