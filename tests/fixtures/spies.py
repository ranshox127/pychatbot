import pytest
from dependency_injector import providers

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
