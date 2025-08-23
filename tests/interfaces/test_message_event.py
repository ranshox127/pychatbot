# uv run -m pytest tests/interfaces/test_message_event.py
from unittest.mock import ANY
from tests.helpers import make_base_envelope, ev_message_text, post_line_event


def test_message_register_flow(client, app, container, mysql_tx, seed_student):
    # 未註冊（收到訊息 -> 當作註冊學號）
    seed_student(student_id="S77777777", user_id="U_NEW", registered=False)

    payload = make_base_envelope(
        ev_message_text(text="S77777777", user_id="U_NEW"))
    resp, _ = post_line_event(client, app, payload)
    assert resp.status_code == 200

    # 驗證 DB 狀態變更或 RegistrationService 呼叫（視你的實作）
    # 例如查 DB：students.registered=1（略）


def test_message_logged_and_routes_by_state(client, app, container, mysql_tx, seed_student):
    # 已註冊學生 -> 會 log_message -> 依 state 分派
    seed_student(student_id="S12345678", user_id="U_OK", registered=True)

    payload = make_base_envelope(
        ev_message_text(text="助教安安，我有問題!", user_id="U_OK"))
    resp, _ = post_line_event(client, app, payload)
    assert resp.status_code == 200

    # 檢查：message_log/狀態遷移/ask_ta_service.start_inquiry 被呼叫（看你是否 mock 或查 DB）
