# tests/fixtures/db_tx.py
import pytest
import pymysql

def _connect_mysql(cfg):
    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["db"],
        port=cfg.get("port", 3306),
        autocommit=False,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

@pytest.fixture
def linebot_mysql_tx(container):
    cfg = container.config.LINEBOT_DB_CONFIG()
    conn = _connect_mysql(cfg)
    try:
        conn.begin()
        yield conn
    finally:
        # 連線可能已被 repo 關掉了，做保護
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

@pytest.fixture
def rs_mysql_tx(container):
    cfg = container.config.REVIEW_SYSTEM_DB_CONFIG()
    conn = _connect_mysql(cfg)
    try:
        conn.begin()
        yield conn
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

@pytest.fixture
def verify_mysql_tx(container):
    cfg = container.config.VERIFY_DB_CONFIG()
    conn = _connect_mysql(cfg)
    try:
        conn.begin()
        yield conn
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
