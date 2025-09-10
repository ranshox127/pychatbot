# uv run -m pytest tests/interfaces/test_postback_event.py
import pytest

from domain.user_state import UserStateEnum
from interfaces.postback_parser import parse_postback
from tests.helpers import (
    client_post_event, ev_postback, make_base_envelope, wait_for)


def test_postback_event_parse():
    """
    Postback 解析
    parse_postback 能正確解析事件資料
    parsed.action / parsed.ns 能正確分流
    """
    fake_line_payload = ev_postback(data="apply_leave")

    data = fake_line_payload["postback"]['data']

    parsed = parse_postback(data)

    assert parsed.action == "apply_leave"
    assert parsed.ns is None


@pytest.mark.parametrize(
    "data,expect_called",
    [
        ("apply_leave", "leave_apply"),
        ("fetch_absence_info", "attendance"),
        ("check_homework", "score_publish"),
        ("action:confirm_leave", "leave_reason"),
        ("action:cancel", "cancel_idle"),
    ],
)
@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_postback_triggers_expected_service(client, app,
                                            it_seed_student, chatbot_logger_spy, service_spies, user_state_spy,
                                            data, expect_called):

    course_title = "1132_程式設計-Python_黃鈺晴教師"
    line_id = 'test_id'
    student_id = '114514'
    name = 'owen'

    it_seed_student(
        user_id=line_id,
        student_id=student_id,
        name=name,
        context_title=course_title,
    )

    payload = make_base_envelope(ev_postback(data=data, user_id=line_id))

    resp, _ = client_post_event(client, app, payload)

    assert resp.status_code == 200

    assert wait_for(lambda: any(m.get("message") == data for m in chatbot_logger_spy.messages)
                    ), f"message 未處理：messages={chatbot_logger_spy.messages}"

    # ---- Assert: branch-specific ----
    mapping = {
        "leave_apply":   ("leave", "apply_for_leave"),
        "attendance":    ("attendance", "check_attendance"),
        "score_publish": ("score", "check_publish_contents"),
        "leave_reason":  ("leave", "ask_leave_reason"),
        "cancel_idle":   ("state", "set_state"),
    }
    svc, method = mapping[expect_called]

    if svc == "state":
        assert wait_for(lambda: user_state_spy.called(
            "set_state")), "預期呼叫 set_state，但沒有"
        c = user_state_spy.last_call("set_state")
        assert c.args == (line_id, UserStateEnum.IDLE)
        return

    spy = service_spies[svc]
    assert wait_for(lambda: spy.called(method), timeout=2.0), \
        f"預期呼叫 {svc}.{method}，但沒有；calls={spy.calls}"
    call = spy.last_call(method)

    if method in ("apply_for_leave", "check_attendance", "check_publish_contents", "ask_leave_reason"):
        assert call.kwargs.get("reply_token") == "test_reply_token_123"
    if method == "ask_leave_reason":
        # 建議：避免硬寫 1，可改為「存在且為正整數」
        msg_id = call.kwargs.get("message_log_id")
        assert isinstance(msg_id, int) and msg_id > 0
