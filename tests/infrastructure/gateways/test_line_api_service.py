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

pytestmark = pytest.mark.contract


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


@pytest.mark.parametrize(
    "method_name, message",
    [
        ("reply_message", TextMessage(text="Single Reply")),
        ("push_message", TextMessage(text="Single Push"))
    ]
)
def test_single_message_acceptance(service, mock_messaging_api, method_name, message):
    """測試單一訊息的處理"""
    method = getattr(service, method_name)
    method("token-1", message)

    req = mock_messaging_api.reply_message.call_args[0][
        0] if method_name == "reply_message" else mock_messaging_api.push_message.call_args[0][0]
    assert isinstance(req, ReplyMessageRequest if method_name ==
                      "reply_message" else PushMessageRequest)
    assert len(req.messages) == 1
    assert req.messages[0].text == message.text


@pytest.mark.parametrize(
    "method_name, token, message, expected_request_type, expected_texts",
    [
        ("reply_message", "token-2", [TextMessage(text="A"),
         TextMessage(text="B")], ReplyMessageRequest, ["A", "B"]),
        ("push_message", "U123456789", [TextMessage(
            text="Hi")], PushMessageRequest, ["Hi"])
    ]
)
def test_list_message_acceptance(service, mock_messaging_api, method_name, token, message, expected_request_type, expected_texts):
    """測試單一訊息的處理"""
    method = getattr(service, method_name)
    method(token, message)

    # 根據 method_name 取得對應的 API 呼叫
    if method_name == "reply_message":
        req = mock_messaging_api.reply_message.call_args[0][0]
    else:
        req = mock_messaging_api.push_message.call_args[0][0]

    # 驗證請求的類型
    assert isinstance(req, expected_request_type)

    # 驗證訊息內容
    assert [m.text for m in req.messages] == expected_texts


def test_reply_text_message_builds_payload_and_calls_sdk(service, mock_messaging_api):
    service.reply_text_message("reply-token-123", "Hello!")

    mock_messaging_api.reply_message.assert_called_once()
    req = mock_messaging_api.reply_message.call_args[0][0]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == "reply-token-123"
    assert len(req.messages) == 1
    assert isinstance(req.messages[0], TextMessage)
    assert req.messages[0].text == "Hello!"


def test_link_rich_menu_to_user_success(service, mock_messaging_api, capsys):
    service.link_rich_menu_to_user("U123", "main_menu")

    mock_messaging_api.link_rich_menu_id_to_user.assert_called_once_with(
        "U123", "richmenu-123"
    )


def test_link_rich_menu_to_user_unknown_alias_no_call(service, mock_messaging_api, capsys):
    service.link_rich_menu_to_user("U123", "unknown_menu")

    # 不應呼叫 SDK，僅印出 debug 訊息後返回
    mock_messaging_api.link_rich_menu_id_to_user.assert_not_called()
