# tests/fixtures/mysql_fixtures.py
import os
import types
import pytest
import pymysql


def _db(name):
    return {
        "host": os.getenv("CHATBOT_DB_HOST", "127.0.0.1"),
        "user": os.getenv("CHATBOT_DB_USER", "root"),
        "password": os.getenv("CHATBOT_DB_PASSWORD", "root"),
        # LINEBOT_DB_NAME / VERIFY_DB_NAME / REVIEW_SYSTEM_DB_NAME
        "db": os.getenv(name),
        "port": int(os.getenv("CHATBOT_DB_PORT", "3306")),
    }


@pytest.fixture(scope="session")
def test_config():
    cfg = types.SimpleNamespace()
    cfg.LINEBOT_DB_CONFIG = _db("LINEBOT_DB_NAME")
    cfg.VERIFY_DB_CONFIG = _db("VERIFY_DB_NAME")
    cfg.REVIEW_SYSTEM_DB_CONFIG = _db("REVIEW_SYSTEM_DB_NAME")
    return cfg


def _mysql_autocommit(cfg):
    return pymysql.connect(
        host=cfg["host"], user=cfg["user"], password=cfg["password"],
        database=cfg["db"], port=cfg.get("port", 3306),
        autocommit=True, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def _safe_truncate(cur, table):
    try:
        cur.execute(f"TRUNCATE TABLE `{table}`")
    except pymysql.err.ProgrammingError:
        pass


LINEBOT_TABLES = [
    "course_info", "account_info", "user_states",
    "message_logs", "event_logs", "change_HW_deadline", "ask_for_leave",
    "summary_gradding_log",
]

REVIEW_TABLES = [
    "review_publish",
]

VERIFY_TABLES = [
    "SummarySubmissions",
]


@pytest.fixture
def linebot_mysql_conn(test_config):
    return _mysql_autocommit(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture
def review_mysql_conn(test_config):
    return _mysql_autocommit(test_config.REVIEW_SYSTEM_DB_CONFIG)


@pytest.fixture
def verify_mysql_conn(test_config):
    return _mysql_autocommit(test_config.VERIFY_DB_CONFIG)


@pytest.fixture
def linebot_clean(linebot_mysql_conn):
    with linebot_mysql_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in LINEBOT_TABLES:
            _safe_truncate(cur, t)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    yield linebot_mysql_conn
    with linebot_mysql_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in LINEBOT_TABLES:
            _safe_truncate(cur, t)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")


@pytest.fixture
def review_clean(review_mysql_conn):
    with review_mysql_conn.cursor() as cur:
        for t in REVIEW_TABLES:
            _safe_truncate(cur, t)
    yield review_mysql_conn
    with review_mysql_conn.cursor() as cur:
        for t in REVIEW_TABLES:
            _safe_truncate(cur, t)


@pytest.fixture
def verify_clean(verify_mysql_conn):
    with verify_mysql_conn.cursor() as cur:
        for t in VERIFY_TABLES:
            _safe_truncate(cur, t)
    yield verify_mysql_conn
    with verify_mysql_conn.cursor() as cur:
        for t in VERIFY_TABLES:
            _safe_truncate(cur, t)
