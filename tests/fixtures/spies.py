import pytest
from dependency_injector import providers


# ---- line_service Spy：收集 reply_text_message ----
class LineApiServiceSpy:
    def __init__(self):
        self.replies = []   # [{"reply_token": str, "text": str}]
        self.pushed = []    # [{"user_id": str, "messages": list}]
        self.linked = []    # [{"user_id": str, "menu_alias": str}]

    def reply_text_message(self, reply_token: str, text: str):
        self.replies.append({"reply_token": reply_token, "text": text})

    def reply_message(self, reply_token: str, messages):
        # 收斂成文字方便斷言；若是 SDK 物件就抓 text 屬性
        if not isinstance(messages, list):
            messages = [messages]
        for m in messages:
            txt = getattr(m, "text", repr(m))
            self.replies.append({"reply_token": reply_token, "text": txt})

    def push_message(self, user_id: str, messages):
        self.pushed.append({"user_id": user_id, "messages": messages})

    def link_rich_menu_to_user(self, user_id: str, menu_alias: str):
        self.linked.append({"user_id": user_id, "menu_alias": menu_alias})


@pytest.fixture
def line_api_service_spy(container):
    spy = LineApiServiceSpy()
    container.line_api_service.override(providers.Object(spy))
    try:
        # 如果 registration_service 是 Singleton 之類才需要 reset；
        # 在 Factory 情況下沒有 reset，就直接跳過
        maybe_reset = getattr(
            getattr(container, "registration_service", None), "reset", None)
        if callable(maybe_reset):
            maybe_reset()
        yield spy
    finally:
        container.line_api_service.reset_override()

# --- Mail spy -------------------------------------------------


class MailCarrierSpy:
    def __init__(self):
        # list of dicts: {"to": [...], "content": LeaveEmailContent}
        self.sent = []

    def send_email(self, to, content):
        self.sent.append({"to": to, "content": content})


@pytest.fixture
def mail_spy(container):
    """覆寫 container.mail_carrier，回傳可檢查的 spy。"""
    spy = MailCarrierSpy()
    container.mail_carrier.override(
        providers.Object(spy))  # pylint: disable=no-member
    try:
        yield spy
    finally:
        container.mail_carrier.reset_override()


# ---- logger Spy：記錄 log_event ----
class ChatbotLoggerSpy:
    def __init__(self):
        self._next_id = 1
        self.messages = []
        self.events = []

    def log_message(self, **kwargs) -> int:
        mid = self._next_id
        self._next_id += 1
        self.messages.append({"id": mid, **kwargs})
        return mid

    def log_event(self, **kwargs):
        self.events.append(kwargs)


@pytest.fixture
def chatbot_logger_spy(container):
    spy = ChatbotLoggerSpy()
    container.chatbot_logger.override(providers.Object(spy))
    try:
        # ⭐ 重要：強制丟棄既有單例，讓之後取得時重建並注入新的 spy
        if hasattr(container, "check_score_service"):
            try:
                # Singleton / Factory 都可呼叫，Singleton 會清快取
                container.check_score_service.reset()
            except Exception:
                pass
        yield spy
    finally:
        container.chatbot_logger.reset_override()


# --- Leave repo spy（包 real repo，保留寫入 + 計次） ----------------------------
class LeaveRepoSpy:
    def __init__(self, real_repo):
        self.real = real_repo
        self.calls = 0

    def save_leave_request(self, leave):
        self.calls += 1
        return self.real.save_leave_request(leave)

    def __getattr__(self, name):
        return getattr(self.real, name)


@pytest.fixture
def leave_repo_spy(container):
    """覆寫 container.leave_repo，保留真實寫入，但可觀察呼叫次數。"""
    real = container.leave_repo()
    spy = LeaveRepoSpy(real)
    container.leave_repo.override(
        providers.Object(spy))  # pylint: disable=no-member
    try:
        yield spy
    finally:
        container.leave_repo.reset_override()


# ---- score_aggregator Stub：回傳可被 format 的簡單物件或讓 format 被猴補忽略 ----
class ScoreAggregatorStub:
    def __init__(self):
        self.calls = []

    def aggregate(self, *, student, course, unit_name, mistake_review_sheet_url):
        self.calls.append({
            "student": student,
            "course": course,
            "unit_name": unit_name,
            "mistake_review_sheet_url": mistake_review_sheet_url,
        })
        # 回傳什麼都可以，因為我們會 monkeypatch _format_score_report
        return object()


@pytest.fixture
def score_aggregator_stub(container):
    stub = ScoreAggregatorStub()
    container.score_aggregator.override(
        providers.Object(stub))  # pylint: disable=no-member
    try:
        yield stub
    finally:
        container.score_aggregator.reset_override()
