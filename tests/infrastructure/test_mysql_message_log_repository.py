# uv run -m pytest tests/infrastructure/test_mysql_message_log_repository.py
from datetime import datetime
import pytest
from infrastructure.mysql_message_log_repository import MySQLMessageLogRepository
from domain.message_log import MessageLog

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def repo(test_config):
    return MySQLMessageLogRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean):
    yield


def test_save_event_log_inserts_correctly(repo, linebot_clean):
    message_log = MessageLog(
        datetime.now(),
        "114514",
        "身體不適",
        "1122_程式設計-Python_黃鈺晴教師"
    )
    
    repo.save_message_log(message_log)

    with linebot_clean.cursor() as cur:
        cur.execute("SELECT * FROM message_logs ORDER BY log_id DESC LIMIT 1")
        row = cur.fetchone()
        assert row is not None
        assert row["student_ID"] == message_log.student_id
        assert row["message"] == message_log.message
