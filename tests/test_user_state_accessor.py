# uv run -m pytest tests/test_user_state_accessor.py
from unittest.mock import MagicMock

from application.user_state_accessor import UserStateAccessor
from domain.user_state import UserState, UserStateEnum


def test_get_state_returns_existing_state():
    mock_repo = MagicMock()
    mock_repo.get.return_value = UserState(
        "U123", UserStateEnum.AWAITING_TA_QUESTION)

    accessor = UserStateAccessor(mock_repo)

    result = accessor.get_state("U123")

    assert result == UserStateEnum.AWAITING_TA_QUESTION
    mock_repo.get.assert_called_once_with("U123")


def test_get_state_returns_idle_if_none():
    mock_repo = MagicMock()
    mock_repo.get.return_value = None

    accessor = UserStateAccessor(mock_repo)
    result = accessor.get_state("U123")

    assert result == UserStateEnum.IDLE


def test_set_state_creates_new_state_if_none():
    mock_repo = MagicMock()
    mock_repo.get.return_value = None

    accessor = UserStateAccessor(mock_repo)
    accessor.set_state("U123", UserStateEnum.AWAITING_LEAVE_REASON)

    # 檢查 save() 被呼叫，且內容正確
    args = mock_repo.save.call_args[0][0]  # 第一個參數
    assert args.line_user_id == "U123"
    assert args.status == UserStateEnum.AWAITING_LEAVE_REASON
