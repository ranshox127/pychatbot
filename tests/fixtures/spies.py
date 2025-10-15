from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List
import pytest
from dependency_injector import providers


# ---- line_service Spy：收集 reply_text_message ----
class LineApiServiceSpy:
    """
    drop-in 取代 infrastructure/gateways/line_api_service.LineApiService
    不呼叫外部網路，只記錄呼叫內容以供斷言。
    """

    def __init__(self, line_rich_menus: Dict[str, str] | None = None):
        self.line_rich_menus = line_rich_menus or {}
        # 記錄
        # {"reply_token": str, "texts": [str], "raw_messages": list}
        self.replies: list[dict[str, Any]] = []
        # {"user_id": str, "raw_messages": list}
        self.pushed:  list[dict[str, Any]] = []
        # {"user_id": str, "menu_alias": str, "menu_id": str}
        self.linked:  list[dict[str, str]] = []
        # 統計（有需要可用）
        self.reply_count = 0
        self.push_count = 0
        self.link_count = 0

    # 與正式碼相同的方法簽章
    def reply_message(self, reply_token: str, messages: List[Any]):
        if not isinstance(messages, list):
            messages = [messages]
        # 收斂成純文字方便斷言；保留 raw 以便需要更細查驗
        texts = []
        for m in messages:
            txt = getattr(m, "text", None)
            if txt is None:
                txt = getattr(m, "alt_text", None)
            if txt is None:
                txt = repr(m)
            texts.append(txt)
        self.replies.append({"reply_token": reply_token,
                            "texts": texts, "raw_messages": messages})
        self.reply_count += 1

    def reply_text_message(self, reply_token: str, text: str):
        # 正式碼會轉 TextMessage 再呼叫 reply_message；Spy 直接記錄字串
        self.replies.append({"reply_token": reply_token,
                            "texts": [text], "raw_messages": []})
        self.reply_count += 1

    def push_message(self, user_id: str, messages: List[Any]):
        if not isinstance(messages, list):
            messages = [messages]
        self.pushed.append({"user_id": user_id, "raw_messages": messages})
        self.push_count += 1

    def link_rich_menu_to_user(self, user_id: str, menu_alias: str):
        menu_id = self.line_rich_menus.get(menu_alias)
        # 與正式碼一致：若找不到 alias，直接不動作
        if not menu_id:
            return
        self.linked.append(
            {"user_id": user_id, "menu_alias": menu_alias, "menu_id": menu_id})
        self.link_count += 1

    # 小工具
    def reset(self):
        self.replies.clear()
        self.pushed.clear()
        self.linked.clear()
        self.reply_count = self.push_count = self.link_count = 0


@pytest.fixture
def line_api_service_spy(container):
    # 你可以從設定抓真正的 mapping；這裡先給預設
    rich_menus = {"main": "richmenu-main-id-for-test",
                  "registration": "richmenu-registration-id-for-test"}
    spy = LineApiServiceSpy(line_rich_menus=rich_menus)

    # 覆寫：讓 container.line_api_service() 直接回傳 Spy
    container.line_api_service.override(providers.Object(spy))
    try:
        spy.reset()
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


class StudentRepoStub:
    def __init__(self):
        # 依你的介面擴充需要的方法；這裡先處理 find_by_line_id
        self._by_line_id = {}

    def set_find_by_line_id(self, line_id, student_or_none):
        self._by_line_id[line_id] = student_or_none

    def find_by_line_id(self, line_id: str):
        return self._by_line_id.get(line_id)


@pytest.fixture
def student_repo_stub(container):
    stub = StudentRepoStub()
    container.student_repo.override(providers.Object(stub))
    try:
        yield stub
    finally:
        container.student_repo.reset_override()


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


@dataclass
class Call:
    method: str
    args: tuple
    kwargs: dict


class UserStateAccessorSpy:
    """可預置 user 狀態，並記錄 get/set 呼叫。"""

    def __init__(self, default_state=None):
        # default_state 可依你的系統預設，例如 UserStateEnum.IDLE
        self._states = {}     # user_id -> UserStateEnum
        self._default = default_state
        self.calls = []
        self.calls_by_method = defaultdict(list)

    # 測試輔助：手動設定某個 user 的狀態
    def set_user_state(self, user_id, state):
        self._record("set_user_state", user_id, state)
        self._states[user_id] = state

    # 正式介面：get_state / set_state
    def get_state(self, user_id):
        self._record("get_state", user_id)
        return self._states.get(user_id, self._default)

    def set_state(self, user_id, state):
        self._record("set_state", user_id, state)
        self._states[user_id] = state

    # 小工具
    def _record(self, method, *args, **kwargs):
        c = Call(method, args, kwargs)
        self.calls.append(c)
        self.calls_by_method[method].append(c)
        return c

    def called(self, method: str) -> bool:
        return len(self.calls_by_method.get(method, [])) > 0

    def last_call(self, method: str | None = None) -> Call | None:
        if method is None:
            return self.calls[-1] if self.calls else None
        lst = self.calls_by_method.get(method, [])
        return lst[-1] if lst else None


# pytest fixture：覆寫 container.user_state_accessor
@pytest.fixture
def user_state_spy(container):
    spy = UserStateAccessorSpy(default_state=None)  # 依系統預設放 IDLE 也可以
    container.user_state_accessor.override(providers.Object(spy))
    try:
        yield spy
    finally:
        container.user_state_accessor.reset_override()


class ProxySpy:
    """包一個 real 物件，攔截任意方法呼叫並記錄。"""

    def __init__(self, real=None, service_name: str = ""):
        self._real = real
        self._service_name = service_name
        self.calls = []                 # 依序記錄
        self.calls_by_method = defaultdict(list)

    def __getattr__(self, name):
        real_attr = getattr(self._real, name, None)

        def _spy_method(*args, **kwargs):
            c = Call(method=name, args=args, kwargs=kwargs)
            self.calls.append(c)
            self.calls_by_method[name].append(c)
            # 需要真的執行 real 時就放行；不需要就直接 return None
            if callable(real_attr):
                return real_attr(*args, **kwargs)
            return real_attr
        return _spy_method

    # 小工具
    def called(self, method: str) -> bool:
        return len(self.calls_by_method.get(method, [])) > 0

    def last_call(self, method: str | None = None) -> Call | None:
        if method is None:
            return self.calls[-1] if self.calls else None
        lst = self.calls_by_method.get(method, [])
        return lst[-1] if lst else None


@pytest.fixture
def service_spies(container):
    """一次裝好四個 service 的 Spy，回傳 dict 方便取用。"""
    # 取出 real（如果你不想真的執行，可改成 real=None）
    leave_real = container.leave_service()
    att_real = container.check_attendance_service()
    score_real = container.check_score_service()
    askta_real = container.ask_ta_service()

    # 對於 registration_service，本測試只需要記錄呼叫，不需要真的執行 → real=None
    try:
        reg_provider = getattr(container, "registration_service")
        reg_real = None  # 僅記錄呼叫，不放行到真實實作
    except AttributeError:
        reg_real = None

    leave_spy = ProxySpy(leave_real, "leave")
    att_spy = ProxySpy(att_real,   "attendance")
    score_spy = ProxySpy(score_real, "score")
    askta_spy = ProxySpy(askta_real, "ask_ta")
    reg_spy = ProxySpy(reg_real,   "registration")

    # 覆寫
    container.leave_service.override(providers.Object(leave_spy))
    container.check_attendance_service.override(providers.Object(att_spy))
    container.check_score_service.override(providers.Object(score_spy))
    container.ask_ta_service.override(providers.Object(askta_spy))
    if hasattr(container, "registration_service"):
        container.registration_service.override(providers.Object(reg_spy))

    # 若上層是 Singleton，重建以吃到新依賴
    for name in ("check_score_service", ):
        prov = getattr(container, name, None)
        if hasattr(prov, "reset"):
            try:
                prov.reset()
            except Exception:
                pass

    try:
        spies = {
            "leave": leave_spy,
            "attendance": att_spy,
            "score": score_spy,
            "ask_ta": askta_spy
        }
        if hasattr(container, "registration_service"):
            spies["registration"] = reg_spy
        yield spies
    finally:
        container.leave_service.reset_override()
        container.check_attendance_service.reset_override()
        container.check_score_service.reset_override()
        container.ask_ta_service.reset_override()
        if hasattr(container, "registration_service"):
            container.registration_service.reset_override()


class FuncSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})

    def called(self): return bool(self.calls)
    def last(self): return self.calls[-1] if self.calls else None
    def clear(self): self.calls.clear()


class FakeExecutor:
    def __init__(self):
        self.submits = []
        self.raise_on_submit = None

    def submit(self, fn, *args, **kwargs):
        if self.raise_on_submit:
            raise self.raise_on_submit
        self.submits.append({"fn": fn, "args": args, "kwargs": kwargs})
        # 不啟動 thread，純記錄
