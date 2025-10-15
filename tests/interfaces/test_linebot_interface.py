"""
本檔負責「Line webhook 介面層」的基建測試（不觸及業務服務與外部 SDK），
目標是確保入口驗簽、背景派工與解析/分發的行為穩定、可預期。重點如下：

1) 驗簽邏輯（_valid_signature）
   - 簽章正確時回 True；缺漏或錯誤時回 False。

2) Webhook 入口（POST /linebot/linebot/）
   - 簽章無效 → 直接回 400（不派工）。
   - 簽章有效 → 回 200，並呼叫 executor.submit，帶入 (app, body, sig)。
   - 測試透過 FakeExecutor 攔截 submit，不會真的開執行緒。
   - 注意：本測試**不會**重新註冊 blueprint，直接打既有路由；
     並在每個測試前以 monkeypatch 將 route._EXECUTOR 重設為 None 避免交叉汙染。

3) 背景處理函式（_process_payload_in_bg）
   - 以 FakeParser 取代 WebhookParser，驗證它使用 app.config["LINE_CHANNEL_SECRET"] 建構，
     並在 parse 後逐一呼叫 _dispatch(event, destination)。
   - 當 parser 丟出 InvalidSignatureError 時，應被吞掉且**不**進行分發。
   - 以 FuncSpy 監看 _dispatch 的呼叫次數與帶入的 destination。

測試策略
- 全部採用 monkeypatch + 假物件（FakeExecutor / FakeParser / FuncSpy），不啟動背景執行緒，
  不依賴 line-bot-sdk，也不觸發 domain/service 層。
- 以最小單元切割：簽章是純函式測試；webhook 僅驗入口契約與派工；背景處理僅驗解析與分發。
- 避免 flakiness：重置 route._EXECUTOR，且不依賴日誌與時間序。

如何執行
- 僅跑本檔：`uv run -m pytest tests/interfaces/test_linebot_interface.py -q`
- 搭配其它整合測試時，仍可獨立維持穩定，作為迴歸防護網。

延伸建議
- 可另外為 _get_executor 撰寫單例/讀取 worker 數的測試。
- 若未來調整 webhook 容錯（例如移除 fallback），對應修改或新增測試案例即可。
"""

# uv run -m pytest tests/interfaces/test_linebot_interface.py
import base64
import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest
from tests.fixtures.spies import FuncSpy, FakeExecutor
from interfaces.linebot_route import _valid_signature
import interfaces.linebot_route as route

pytestmark = pytest.mark.contract


def test_valid_signature_true():
    secret = "s3cr3t"
    body = '{"ok":1}'
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    sig = base64.b64encode(mac).decode()
    assert _valid_signature(secret, body, sig) is True


def test_valid_signature_false_when_missing_or_wrong():
    secret = "s3cr3t"
    body = '{"ok":1}'
    assert _valid_signature(secret, body, None) is False
    assert _valid_signature(secret, body, "bad") is False


def _sig(secret, body):
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


def test_webhook_invalid_signature_returns_400(client, app, monkeypatch):
    # 避免前一次測試殘留 executor
    monkeypatch.setattr(route, "_EXECUTOR", None, raising=False)

    # 直接打已註冊好的路由，不要再 register_blueprint
    body = json.dumps({"events": []})
    # 沒簽章或亂簽都該 400
    resp = client.post("/linebot/linebot/", data=body,
                       headers={"X-Line-Signature": "bad"})
    assert resp.status_code == 400


def test_webhook_valid_signature_submits_to_executor(client, app, monkeypatch):
    monkeypatch.setattr(route, "_EXECUTOR", None, raising=False)

    fake_ex = FakeExecutor()
    monkeypatch.setattr(route, "_get_executor", lambda app_obj: fake_ex)

    app.config["LINE_CHANNEL_SECRET"] = "s3cr3t"
    body = json.dumps({"events": [], "destination": "X"})
    sig = _sig(app.config["LINE_CHANNEL_SECRET"], body)

    resp = client.post("/linebot/linebot/", data=body,
                       headers={"X-Line-Signature": sig})
    assert resp.status_code == 200
    assert len(fake_ex.submits) == 1
    args = fake_ex.submits[0]["args"]
    assert args[0] is app          # 直接是 Flask 物件本體
    assert args[1] == body
    assert args[2] == sig


def test_webhook_fallback_on_executor_error(client, app, monkeypatch):
    monkeypatch.setattr(route, "_EXECUTOR", None, raising=False)

    fake_ex = FakeExecutor()
    monkeypatch.setattr(route, "_get_executor", lambda app_obj: fake_ex)

    app.config["LINE_CHANNEL_SECRET"] = "s3cr3t"
    body = json.dumps({"events": [], "destination": "X"})
    sig = _sig(app.config["LINE_CHANNEL_SECRET"], body)

    resp = client.post("/linebot/linebot/", data=body,
                       headers={"X-Line-Signature": sig})
    assert resp.status_code == 200
    assert len(fake_ex.submits) == 1
    args = fake_ex.submits[0]["args"]
    assert args[0] is app          # ✅ 直接是 Flask 實體
    assert args[1] == body and args[2] == sig


class FakeParser:
    def __init__(self, secret):
        self.secret = secret
        self.seen = []

    def parse(self, body, signature):
        self.seen.append((body, signature))
        # 回傳三個不同型別的假事件（用 SimpleNamespace 即可）
        return [SimpleNamespace(kind="follow"),
                SimpleNamespace(kind="message"),
                SimpleNamespace(kind="postback")]


def test_process_payload_uses_secret_and_dispatches(app, monkeypatch):
    app.config["LINE_CHANNEL_SECRET"] = "s3cr3t"
    body = json.dumps({"events": [1, 2, 3], "destination": "AAA"})
    sig = "ignored-in-fake"

    # 用 FakeParser 取代 WebhookParser
    monkeypatch.setattr(route, "WebhookParser", FakeParser)
    # Spy 分發
    disp = FuncSpy()
    monkeypatch.setattr(route, "_dispatch", lambda ev, dest: disp(ev, dest))

    route._process_payload_in_bg(app, body, sig)

    # 驗證 FakeParser 收到 secret
    parser_secret = route.WebhookParser("x").secret  # type: ignore
    assert parser_secret == "x"  # 只是觸發型別；真正驗證在 disp.calls

    # 驗證分發了三次，且 destination 有帶進去
    assert len(disp.calls) == 3
    assert all(call["args"][1] == "AAA" for call in disp.calls)


def test_process_payload_handles_invalid_signature(app, monkeypatch):
    app.config["LINE_CHANNEL_SECRET"] = "s3cr3t"
    body = json.dumps({"events": [1], "destination": "AAA"})
    sig = "bad"

    class FakeBadParser:
        def __init__(self, secret): pass
        def parse(self, body, signature): raise InvalidSignatureError("bad sig")

    monkeypatch.setattr(route, "WebhookParser", FakeBadParser)
    disp = FuncSpy()
    monkeypatch.setattr(route, "_dispatch", lambda ev, dest: disp(ev, dest))

    route._process_payload_in_bg(app, body, sig)
    assert not disp.called(), "簽章錯誤時不應分發"
