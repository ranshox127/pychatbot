# tests/fixtures/mysql_fixtures.py
import pytest
import pymysql


@pytest.fixture
def mysql_conn(test_config):
    print(f"[DEBUG-MYSQL-FIXTURE] Connecting to {test_config.LINEBOT_DB_CONFIG['host']}:{test_config.LINEBOT_DB_CONFIG.get('port', 3306)} "
          f"user={test_config.LINEBOT_DB_CONFIG['user']} "
          f"db={test_config.LINEBOT_DB_CONFIG['db']}")
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
