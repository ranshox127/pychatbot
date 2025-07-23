# tests/test_mysql_user_state_repository.py
# uv run -m pytest tests/test_mysql_user_state_repository.py
import pytest
import pymysql
from infrastructure.mysql_user_state_repository import MySQLUserStateRepository
from domain.user_state import UserState, UserStateEnum


@pytest.fixture(scope="module")
def db_config():
    return {
        "host": '140.115.53.151',
        "user": "kslab",
        "password": 'Kslab35356!',
        "db": "linebot_test",
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.Cursor,
        "autocommit": True,
    }


@pytest.fixture()
def repo(db_config):
    user_state_repo = MySQLUserStateRepository(db_config)

    # 每個測試前清除目標用戶資料
    with user_state_repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_states WHERE line_user_id = 'U_test'")
            conn.commit()

    yield user_state_repo

    # 測試後清除資料
    with user_state_repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_states WHERE line_user_id = 'U_test'")
            conn.commit()


def test_save_and_get_user_state(repo):
    state = UserState("U_test", UserStateEnum.AWAITING_LEAVE_REASON)
    repo.save(state)

    result = repo.get("U_test")

    assert result is not None
    assert result.line_user_id == "U_test"
    assert result.status == UserStateEnum.AWAITING_LEAVE_REASON


def test_delete_user_state(repo):
    state = UserState("U_test", UserStateEnum.IDLE)
    repo.save(state)

    repo.delete("U_test")
    result = repo.get("U_test")

    assert result is None
