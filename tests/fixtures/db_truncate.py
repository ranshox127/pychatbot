# tests/fixtures/db_truncate.py
import pytest
import pymysql


def _mysql_autocommit(cfg):
    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["db"],
        port=cfg.get("port", 3306),
        autocommit=True,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def _safe_truncate_mysql(cur, table):
    try:
        cur.execute(f"TRUNCATE TABLE `{table}`")
    except pymysql.err.ProgrammingError:
        pass


MYSQL_LINEBOT_TABLES = [
    "course_info", "account_info", "user_states",
    "message_logs", "event_logs", "change_HW_deadline",
    "ask_for_leave",
]


@pytest.fixture
def linebot_mysql_truncate(container):
    """整合測試用：清空 linebot DB 內會用到的表，seed 後 commit。"""
    cfg = container.config.LINEBOT_DB_CONFIG()
    conn = _mysql_autocommit(cfg)
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in MYSQL_LINEBOT_TABLES:
            _safe_truncate_mysql(cur, t)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    yield conn
    # 測試完畢後保持乾淨（可選）
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in MYSQL_LINEBOT_TABLES:
            _safe_truncate_mysql(cur, t)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.close()


@pytest.fixture
def rs_mysql_truncate(container):
    """整合測試用：清空 review-system DB（course repo 會讀）"""
    cfg = container.config.REVIEW_SYSTEM_DB_CONFIG()
    conn = _mysql_autocommit(cfg)
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
