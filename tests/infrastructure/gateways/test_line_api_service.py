# uv run -m pytest tests/infrastructure/gateways/test_line_api_service.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from linebot.v3.messaging import (PushMessageRequest, ReplyMessageRequest,
                                  TextMessage)

from infrastructure.gateways.line_api_service import LineApiService


@pytest.fixture
def mock_messaging_api():
    return MagicMock()


@pytest.fixture
def service(mock_messaging_api):
    return LineApiService(
        line_bot_api=mock_messaging_api,
        channel_access_token="dummy_token",
        line_rich_menus={"main_menu": "richmenu-123"}
    )


def test_reply_text_message(service, mock_messaging_api):
    service.reply_text_message("reply-token-123", "Hello!")

    expected_message = TextMessage(text="Hello!")
    mock_messaging_api.reply_message.assert_called_once()

    args = mock_messaging_api.reply_message.call_args[0][0]
    assert isinstance(args, ReplyMessageRequest)
    assert args.reply_token == "reply-token-123"
    assert args.messages[0].text == "Hello!"


def test_push_message(service, mock_messaging_api):
    msg = TextMessage(text="Hi")
    service.push_message("U123456789", [msg])

    mock_messaging_api.push_message.assert_called_once()
    args = mock_messaging_api.push_message.call_args[0][0]
    assert isinstance(args, PushMessageRequest)
    assert args.to == "U123456789"
    assert args.messages[0].text == "Hi"


def test_link_rich_menu_to_user_success(service):
    with patch("infrastructure.gateways.line_api_service.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        service.link_rich_menu_to_user("U123", "main_menu")
        mock_post.assert_called_once()


def test_link_rich_menu_to_user_no_alias(service, capsys):
    service.link_rich_menu_to_user("U123", "unknown_menu")
    captured = capsys.readouterr()
    assert "No rich menu ID found" in captured.out
