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


@pytest.fixture
def seed_student_data(mysql_conn):
    """清除資料並插入測試用學生資料和課程"""
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE account_info")
        cur.execute("TRUNCATE TABLE course_info")

        cur.execute("""
            INSERT INTO course_info(context_title, status, reserved)
            VALUES('1122_程式設計-Python_黃鈺晴教師', 'in_progress', '')
        """)
        cur.execute("""
            INSERT INTO account_info(student_ID, line_userID, mdl_ID, student_name, context_title, roleid, del)
            VALUES('114514000', 'lineid', 12345, '旅歐文', '1122_程式設計-Python_黃鈺晴教師', 5, 0)
        """)
    yield
