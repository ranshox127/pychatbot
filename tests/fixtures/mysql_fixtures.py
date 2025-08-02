# tests/fixtures/mysql_fixtures.py
import pytest
import pymysql


@pytest.fixture
def mysql_conn(test_config):
    conn = pymysql.connect(
        host=test_config.LINEBOT_DB_CONFIG["host"],
        user=test_config.LINEBOT_DB_CONFIG["user"],
        password=test_config.LINEBOT_DB_CONFIG["password"],
        database=test_config.LINEBOT_DB_CONFIG["db"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    yield conn
    conn.close()

@pytest.fixture
def rs_mysql_conn(test_config):
    conn = pymysql.connect(**test_config.REVIEW_SYSTEM_DB_CONFIG)
    yield conn
    conn.close()
