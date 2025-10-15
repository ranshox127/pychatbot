# uv run -m pytest tests/application/test_user_state_accessor.py
from unittest.mock import MagicMock

import pytest

from application.user_state_accessor import UserStateAccessor
from domain.user_state import UserState, UserStateEnum

pytestmark = pytest.mark.unit


def test_get_state_returns_existing_state():
    """
    Scenario: 使用者有狀態紀錄

    Expect: 回傳對應的狀態
    """
    mock_repo = MagicMock()
    mock_repo.get.return_value = UserState(
        "U123", UserStateEnum.AWAITING_TA_QUESTION)

    accessor = UserStateAccessor(mock_repo)

    result = accessor.get_state("U123")

    assert result == UserStateEnum.AWAITING_TA_QUESTION
    mock_repo.get.assert_called_once_with("U123")


def test_get_state_returns_idle_if_none():
    """
    Scenario: 使用者沒有任何紀錄

    Expect: 預設回傳 IDLE 狀態
    """
    mock_repo = MagicMock()
    mock_repo.get.return_value = None

    accessor = UserStateAccessor(mock_repo)
    result = accessor.get_state("U123")

    assert result == UserStateEnum.IDLE


def test_set_state_creates_new_state_if_none():
    """
    Scenario: 第一次設定狀態

    Expect: 建立新 UserState 並儲存
    """
    mock_repo = MagicMock()
    mock_repo.get.return_value = None

    accessor = UserStateAccessor(mock_repo)
    accessor.set_state("U123", UserStateEnum.AWAITING_LEAVE_REASON)

    # 檢查 save() 被呼叫，且內容正確
    args = mock_repo.save.call_args[0][0]  # 第一個參數
    assert args.line_user_id == "U123"
    assert args.status == UserStateEnum.AWAITING_LEAVE_REASON


def test_set_state_updates_existing_state():
    """
    Scenario: 使用者已存在狀態紀錄

    Expect: 直接更新 status 欄位並呼叫 save()
    """
    existing_state = UserState("U123", UserStateEnum.AWAITING_TA_QUESTION)
    mock_repo = MagicMock()
    mock_repo.get.return_value = existing_state

    accessor = UserStateAccessor(mock_repo)
    accessor.set_state("U123", UserStateEnum.IDLE)

    saved_state = mock_repo.save.call_args[0][0]
    assert saved_state.line_user_id == "U123"
    assert saved_state.status == UserStateEnum.IDLE
