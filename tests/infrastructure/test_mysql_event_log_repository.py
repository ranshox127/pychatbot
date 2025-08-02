# uv run -m pytest tests/infrastructure/test_mysql_event_log_repository.py
from datetime import datetime
import pytest
from infrastructure.mysql_event_log_repository import MySQLEventLogRepository
from domain.event_log import EventLog, EventEnum


@pytest.fixture
def repo(test_config):
    return MySQLEventLogRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_event_logs(mysql_conn):
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE event_logs")
    mysql_conn.commit()


@pytest.mark.parametrize("event_log", [
    EventLog(datetime.now(), "114514", EventEnum.REGISTER,
             None, None, "1122_程式設計-Python_黃鈺晴教師", -1),
    EventLog(datetime.now(), "114514", EventEnum.CHECK_PRESENT,
             None, None, "1122_程式設計-Python_黃鈺晴教師", 11920),
    EventLog(datetime.now(), "114514", EventEnum.CHECK_HOMEWORK,
             None, "C5", "1122_程式設計-Python_黃鈺晴教師", 11924),
    EventLog(datetime.now(), "114514", EventEnum.ASK_FOR_LEAVE,
             None, None, "1122_程式設計-Python_黃鈺晴教師", 11835),
    EventLog(datetime.now(), "114514", EventEnum.CODING_HELP,
             "C5_A2", None, "1122_程式設計-Python_黃鈺晴教師", 11941),
])
def test_save_event_log_inserts_correctly(repo, mysql_conn, event_log):
    repo.save_event_log(event_log)

    with mysql_conn.cursor() as cur:
        cur.execute("SELECT * FROM event_logs ORDER BY log_id DESC LIMIT 1")
        row = cur.fetchone()
        assert row is not None
        assert row["student_ID"] == event_log.student_id
        assert row["operation_event"] == event_log.event_type.value
        assert row["message_log_id"] == event_log.message_log_id
