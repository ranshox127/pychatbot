# uv run -m pytest tests/infrastructure/test_mysql_message_log_repository.py
from datetime import datetime
import pytest
from infrastructure.mysql_message_log_repository import MySQLMessageLogRepository
from domain.message_log import MessageLog


@pytest.fixture
def repo(test_config):
    return MySQLMessageLogRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_message_logs(mysql_conn):
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE message_logs")
    mysql_conn.commit()

    yield

    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE message_logs")
    mysql_conn.commit()


def test_save_event_log_inserts_correctly(repo, mysql_conn):
    message_log = MessageLog(
        datetime.now(),
        "114514",
        "身體不適",
        "1122_程式設計-Python_黃鈺晴教師"
    )
    repo.save_message_log(message_log)

    with mysql_conn.cursor() as cur:
        cur.execute("SELECT * FROM message_logs ORDER BY log_id DESC LIMIT 1")
        row = cur.fetchone()
        assert row is not None
        assert row["student_ID"] == message_log.student_id
        assert row["message"] == message_log.message
