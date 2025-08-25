# tests/fixtures/db_truncate.py
import pytest
import pymysql


def _connect_mysql_autocommit(cfg):
    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["db"],
        port=cfg.get("port", 3306),
        autocommit=True,                      # 關鍵：autocommit
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


@pytest.fixture
def linebot_mysql_truncate(container):
    """整合測試用：清空 linebot DB 內會用到的表，seed 後 commit。"""
    cfg = container.config.LINEBOT_DB_CONFIG()
    conn = _connect_mysql_autocommit(cfg)
    with conn.cursor() as cur:
        # 依你的 schema 補全需要清空的表（注意外鍵順序）
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE course_info")
        cur.execute("TRUNCATE TABLE account_info")
        cur.execute("TRUNCATE TABLE user_states")           # 如果有這張表
        cur.execute("TRUNCATE TABLE message_logs")          # 如果會寫入
        cur.execute("TRUNCATE TABLE event_logs")            # 如果會寫入
        cur.execute("TRUNCATE TABLE change_HW_deadline")   # 會被 course repo 用到
        cur.execute("TRUNCATE TABLE ask_for_leave")  # ← 新增
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    yield conn
    # 測試完畢後保持乾淨（可選）
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE course_info")
        cur.execute("TRUNCATE TABLE account_info")
        cur.execute("TRUNCATE TABLE user_states")
        cur.execute("TRUNCATE TABLE message_logs")
        cur.execute("TRUNCATE TABLE event_logs")
        cur.execute("TRUNCATE TABLE change_HW_deadline")
        cur.execute("TRUNCATE TABLE ask_for_leave")  # ← 新增
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.close()


@pytest.fixture
def rs_mysql_truncate(container):
    """整合測試用：清空 review-system DB（course repo 會讀）"""
    cfg = container.config.REVIEW_SYSTEM_DB_CONFIG()
    conn = _connect_mysql_autocommit(cfg)
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE review_publish")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    yield conn
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE review_publish")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.close()
