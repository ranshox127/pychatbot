# uv run -m pytest tests/interfaces/test_follow_event.py
import pytest
from tests.helpers import make_base_envelope, ev_follow, client_post_event, wait_for

pytestmark = pytest.mark.integration


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_follow_unregistered_triggers_register_prompt(client, app, service_spies):

    user_id = "vhbjnjl"
    payload = make_base_envelope(ev_follow(user_id=user_id))

    # Act
    resp, _ = client_post_event(client, app, payload)
    assert resp.status_code == 200

    reg_spy = service_spies["registration"]
    ok = wait_for(lambda: reg_spy.called("handle_follow_event"), timeout=2.0)
    assert ok, f"未在期限內呼叫 registration.handle_follow_event；calls={reg_spy.calls}"

    call = reg_spy.last_call("handle_follow_event")
    assert call and call.args == (user_id, "test_reply_token_123")
