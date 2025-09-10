# tests/helpers.py
import json
import hmac
import hashlib
import base64
import time
from typing import Dict, Any

import requests


def line_signature(channel_secret: str, body: str) -> str:
    mac = hmac.new(channel_secret.encode("utf-8"),
                   body.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def client_post_event(client, app, payload: Dict[str, Any], path: str = "/linebot/linebot/"):
    """將 payload 轉成正確簽章後送進 Flask。回傳 (response, body_str)。"""
    body_str = json.dumps(payload, separators=(",", ":"))
    sig = line_signature(app.config["LINE_CHANNEL_SECRET"], body_str)
    headers = {"X-Line-Signature": sig, "Content-Type": "application/json"}
    resp = client.post(path, data=body_str, headers=headers)
    return resp, body_str


def outer_post_event(url, secret, payload):
    body_str = json.dumps(payload, separators=(",", ":"))
    sig = line_signature(secret, body_str)
    headers = {"X-Line-Signature": sig, "Content-Type": "application/json"}
    return requests.post(url, data=body_str.encode("utf-8"), headers=headers, timeout=5)


def wait_for(cond, timeout=8.0, interval=0.02):
    """Poll until cond() is True or timeout seconds have elapsed."""
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(interval)
    return False

# ---------- Payload Builders ----------


def make_base_envelope(event: Dict[str, Any]) -> Dict[str, Any]:
    """LINE Webhook 外層 envelope，覆蓋單一事件用。"""
    return {
        "destination": "Uxxxxxxxxxxxxxx",
        "events": [event],
    }


def ev_follow(user_id="U_TEST_USER_ID", reply_token="test_reply_token_123"):
    return {
        "type": "follow",
        "replyToken": reply_token,
        "source": {"userId": user_id, "type": "user"},
        "timestamp": 1609459200000,
        "mode": "active",
        "webhookEventId": "01GXXXXXXXXXXXXXXXXX",
        "deliveryContext": {"isRedelivery": False},
        "follow": {"isUnblocked": False}
    }


def ev_message_text(text="Hello, world", user_id="U_TEST_USER_ID", reply_token="test_reply_token_123"):
    return {
        "type": "message",
        "message": {"type": "text", "quoteToken": "q3Plxr4AgKd...", "id": "14353798921116", "text": text},
        "replyToken": reply_token,
        "source": {"userId": user_id, "type": "user"},
        "timestamp": 1609459200000,
        "mode": "active",
        "webhookEventId": "01GXXXXXXXXXXXXXXXXX",
        "deliveryContext": {"isRedelivery": False},
    }


def ev_postback(data: str, user_id="U_TEST_USER_ID", reply_token="test_reply_token_123"):
    return {
        "type": "postback",
        "postback": {"data": data},
        "replyToken": reply_token,
        "source": {"userId": user_id, "type": "user"},
        "timestamp": 1609459200000,
        "mode": "active",
        "webhookEventId": "01GXXXXXXXXXXXXXXXXX",
        "deliveryContext": {"isRedelivery": False},
    }
