# uv run -m pytest tests/interfaces/test_linebot_route.py
import json
from types import SimpleNamespace
import hmac
import hashlib
import base64
from unittest.mock import MagicMock, ANY


def generate_line_signature(channel_secret: str, request_body: str) -> str:
    """為給定的 request body 產生有效的 LINE Webhook 簽章。"""
    hash_obj = hmac.new(channel_secret.encode('utf-8'),
                        request_body.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(hash_obj).decode('utf-8')


def test_postback_event_for_apply_leave(client, container, app):
    # Arrange：以 mock 替代真實 leave_service
    # 現在 `container` 是正確的 container 實例了
    mock_leave_service = MagicMock()

    fake_student = SimpleNamespace(
        student_id="S12345678",          # 確保長度符合你的 schema
        line_user_id="U_TEST_USER_ID",
        context_title="idle"
    )

    # 【注意】: student repo 也需要 mock，因為 handle_postback 會先查詢 student
    mock_student_repo = MagicMock()
    mock_student_repo.find_by_line_id.return_value = fake_student  # 返回一個模擬的 student 物件

    mock_logger = MagicMock()
    mock_logger.log_message.return_value = 123

    with container.leave_service.override(mock_leave_service), \
            container.student_repo.override(mock_student_repo), \
            container.chatbot_logger.override(mock_logger):

        fake_line_payload = {
            "destination": "Uxxxxxxxxxxxxxx",  # 頂層需要一個 destination 欄位
            "events": [
                {
                    "type": "postback",
                    "replyToken": "test_reply_token_123",
                    "source": {"userId": "U_TEST_USER_ID", "type": "user"},
                    "timestamp": 1609459200000,
                    # --- 補上 Pydantic 要求的必填欄位 ---
                    "mode": "active",
                    "webhookEventId": "01GXXXXXXXXXXXXXXXXX",  # 隨機的假 ID
                    "deliveryContext": {"isRedelivery": False},
                    # ------------------------------------
                    "postback": {
                        "data": "apply_leave"
                    }
                }
            ]
        }

        # 【修正】: 產生有效的 body 和 signature
        body_str = json.dumps(fake_line_payload, separators=(',', ':'))

        # 【確認】確保這裡使用的 secret 來源是 app.config，
        # 它現在會穩定地提供 "this_is_a_fixed_test_secret"
        signature = generate_line_signature(
            app.config['LINE_CHANNEL_SECRET'], body_str
        )

        headers = {'X-Line-Signature': signature}

        # Act：發送假 webhook 至 endpoint
        response = client.post(
            '/linebot/linebot/',  # URL path 根據你的 blueprint 設定
            data=body_str,
            content_type='application/json',
            headers=headers
        )

    # Assert：
    assert response.status_code == 200
    assert response.data == b'OK'

    # 驗證 student repo 被呼叫
    mock_student_repo.find_by_line_id.assert_called_once_with('U_TEST_USER_ID')

    # 驗證 mock service 被正確呼叫
    mock_leave_service.apply_for_leave.assert_called_once_with(
        student=ANY,
        reply_token='test_reply_token_123'
    )
