# uv run -m pytest tests/infrastructure/test_mysql_user_state_repository.py
import pytest
from infrastructure.mysql_user_state_repository import MySQLUserStateRepository
from domain.user_state import UserState, UserStateEnum

pytestmark = pytest.mark.infrastructure


@pytest.fixture()
def repo(test_config):
    return MySQLUserStateRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean):
    yield


def test_save_and_get_user_state(repo, linebot_clean):
    state = UserState("U_test", UserStateEnum.AWAITING_LEAVE_REASON)
    repo.save(state)

    result = repo.get("U_test")

    assert result is not None
    assert result.line_user_id == "U_test"
    assert result.status == UserStateEnum.AWAITING_LEAVE_REASON


def test_delete_user_state(repo, linebot_clean):
    state = UserState("U_test", UserStateEnum.IDLE)
    repo.save(state)

    repo.delete("U_test")
    result = repo.get("U_test")

    assert result is None
