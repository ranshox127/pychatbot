# uv run -m pytest tests/interfaces/test_leave_flow.py
from tests.helpers import make_base_envelope, ev_postback, ev_message_text, post_line_event


def test_leave_full_flow(client, app, container, mysql_tx, seed_student):
    seed_student(student_id="S88888888", user_id="U_FLOW", registered=True)

    # Step 1: 主選單點請假
    resp, _ = post_line_event(client, app, make_base_envelope(
        ev_postback("apply_leave", user_id="U_FLOW")))
    assert resp.status_code == 200
    # 期望：user_state = AWAITING_LEAVE_CONFIRM（查 DB 或 service 記錄）

    # Step 2: 確認請假
    resp, _ = post_line_event(client, app, make_base_envelope(
        ev_postback("[Action]confirm_to_leave", user_id="U_FLOW")))
    assert resp.status_code == 200
    # 期望：user_state = AWAITING_LEAVE_REASON

    # Step 3: 填理由
    resp, _ = post_line_event(client, app, make_base_envelope(
        ev_message_text(text="生病", user_id="U_FLOW")))
    assert resp.status_code == 200
    # 期望：user_state 回到 IDLE，DB 產生請假紀錄


def test_leave_interrupt_then_check_score(client, app, container, mysql_tx, seed_student):
    seed_student(student_id="S99999999", user_id="U_INT", registered=True)

    # 先走到 AWAITING_LEAVE_REASON
    post_line_event(client, app, make_base_envelope(
        ev_postback("apply_leave", user_id="U_INT")))
    post_line_event(client, app, make_base_envelope(
        ev_postback("[Action]confirm_to_leave", user_id="U_INT")))

    # 插話：查分數
    resp, _ = post_line_event(client, app, make_base_envelope(
        ev_postback("check_homework", user_id="U_INT")))
    assert resp.status_code == 200
    # 依你的「政策」驗證 user_state 是否轉為 AWAITING_CONTENTS_NAME 或其他設計
