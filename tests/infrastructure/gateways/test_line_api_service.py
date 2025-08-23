# uv run -m pytest tests/infrastructure/gateways/test_line_api_service.py
from unittest.mock import MagicMock
import pytest
from linebot.v3.messaging import (
    MessagingApi,
    TextMessage,
    ReplyMessageRequest,
    PushMessageRequest,
)
from infrastructure.gateways.line_api_service import LineApiService


@pytest.fixture
def mock_messaging_api():
    # 用 spec 綁定 MessagingApi，避免打錯方法名仍然通過
    return MagicMock(spec=MessagingApi)


@pytest.fixture
def service(mock_messaging_api):
    return LineApiService(
        line_bot_api=mock_messaging_api,
        channel_access_token="dummy_token",
        line_rich_menus={"main_menu": "richmenu-123"},
    )


def test_reply_text_message_builds_payload_and_calls_sdk(service, mock_messaging_api):
    service.reply_text_message("reply-token-123", "Hello!")

    mock_messaging_api.reply_message.assert_called_once()
    req = mock_messaging_api.reply_message.call_args[0][0]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == "reply-token-123"
    assert len(req.messages) == 1
    assert isinstance(req.messages[0], TextMessage)
    assert req.messages[0].text == "Hello!"


def test_reply_message_accepts_single_message(service, mock_messaging_api):
    # 傳入單一 Message 物件，應被包成 list
    msg = TextMessage(text="Single")
    service.reply_message("token-1", msg)

    req = mock_messaging_api.reply_message.call_args[0][0]
    assert isinstance(req, ReplyMessageRequest)
    assert len(req.messages) == 1
    assert req.messages[0].text == "Single"


def test_reply_message_accepts_list(service, mock_messaging_api):
    msgs = [TextMessage(text="A"), TextMessage(text="B")]
    service.reply_message("token-2", msgs)

    req = mock_messaging_api.reply_message.call_args[0][0]
    assert isinstance(req, ReplyMessageRequest)
    assert [m.text for m in req.messages] == ["A", "B"]


def test_push_message_with_list(service, mock_messaging_api):
    msgs = [TextMessage(text="Hi")]
    service.push_message("U123456789", msgs)

    mock_messaging_api.push_message.assert_called_once()
    req = mock_messaging_api.push_message.call_args[0][0]
    assert isinstance(req, PushMessageRequest)
    assert req.to == "U123456789"
    assert len(req.messages) == 1
    assert req.messages[0].text == "Hi"


def test_push_message_accepts_single_message(service, mock_messaging_api):
    msg = TextMessage(text="One")
    service.push_message("U999", msg)

    req = mock_messaging_api.push_message.call_args[0][0]
    assert isinstance(req, PushMessageRequest)
    assert req.to == "U999"
    assert len(req.messages) == 1
    assert req.messages[0].text == "One"


def test_link_rich_menu_to_user_success(service, mock_messaging_api, capsys):
    service.link_rich_menu_to_user("U123", "main_menu")

    mock_messaging_api.link_rich_menu_id_to_user.assert_called_once_with(
        "U123", "richmenu-123"
    )
    out = capsys.readouterr().out
    assert "link_rich_menu_to_user called" in out
    assert "resolved rich_menu_id='richmenu-123'" in out


def test_link_rich_menu_to_user_unknown_alias_no_call(service, mock_messaging_api, capsys):
    service.link_rich_menu_to_user("U123", "unknown_menu")

    # 不應呼叫 SDK，僅印出 debug 訊息後返回
    mock_messaging_api.link_rich_menu_id_to_user.assert_not_called()
    out = capsys.readouterr().out
    assert "link_rich_menu_to_user called" in out
    assert "resolved rich_menu_id=None" in out
