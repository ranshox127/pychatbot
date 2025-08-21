# tests/fixtures/db_tx.py
import pytest
import pymysql

# TODO

@pytest.fixture
def mysql_tx(container):
    # 取得 repo 或直接從 config 建連線
    conn = pymysql.connect(**container.config.LINEBOT_DB_CONFIG())
    try:
        conn.begin()
        yield conn
    finally:
        conn.rollback()
        conn.close()
