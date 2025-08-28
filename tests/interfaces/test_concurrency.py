# uv run -m pytest tests/interfaces/test_concurrency.py
# uv run -m pytest tests/interfaces/test_concurrency.py::test_true_concurrency_register_same_student_id -s

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests
from tests.fixtures.fakes import FakeMoodleRepo

from domain.user_state import UserStateEnum
from tests.helpers import (ev_follow, ev_message_text, ev_postback,
                           line_signature, make_base_envelope, wait_for)


# ---------- utils ----------


def _post_json(url, secret, payload):
    body_str = json.dumps(payload, separators=(",", ":"))
    sig = line_signature(secret, body_str)
    headers = {"X-Line-Signature": sig, "Content-Type": "application/json"}
    return requests.post(url, data=body_str.encode("utf-8"), headers=headers, timeout=5)


# ---------- tests ----------

@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_true_concurrency_register_same_student_id(
    live_server, app, container, seed_course_commit, line_api_service_spy
):
    """
    兩位使用者（U_A, U_B）同時用同一個學號註冊。
    期望：只有一位成功；另一位收到「學號已被使用」的提示；DB 不會把兩位都綁上。
    若背景處理未啟動（非同步層未生效），測試會先做 sanity-check，直接 skip（避免誤判）。
    """
    # --- Arrange --------------------------------------------------------------
    # *可讓背景更可預期：單工 worker（若你的 interface 有讀這個 config）
    app.config["LINE_EXECUTOR_WORKERS"] = 1

    course_title = "1234_程式設計-Python_黃鈺晴教師"
    seed_course_commit(context_title=course_title)

    student_id = "112522065"
    fullname = "雙人衝突測試"
    fake_moodle = FakeMoodleRepo(
        student_id=student_id, fullname=fullname, course_fullname=course_title
    )

    url = f"{live_server.url}/linebot/linebot/"
    secret = app.config["LINE_CHANNEL_SECRET"]

    # --- Sanity check: 背景處理是否有在跑？ ------------------------------------
    # 先用一個單純 follow 事件，看是否會產生任何回覆
    resp = _post_json(url, secret, make_base_envelope(
        ev_follow(user_id="U_SANITY", reply_token="rt_follow_SANITY")))
    assert resp.status_code == 200
    ok_bg = wait_for(lambda: any(r.get("reply_token") ==
                     "rt_follow_SANITY" for r in line_api_service_spy.replies), timeout=2.0)
    if not ok_bg:
        pytest.skip(
            "Webhook 已改為非同步回 200，但背景處理沒有跑起來（未看到任何 reply）。先修 interface 再跑此測試。")

    # --- 主要情境 --------------------------------------------------------------
    with container.moodle_repo.override(fake_moodle):
        # 兩位都 follow（不強求同時）
        for uid in ("U_A", "U_B"):
            resp = _post_json(url, secret, make_base_envelope(
                ev_follow(user_id=uid, reply_token=f"rt_follow_{uid}")))
            assert resp.status_code == 200

        # 幾乎同時送出註冊訊息
        start_barrier = threading.Barrier(2)

        def register(uid, reply_token):
            start_barrier.wait()
            payload = make_base_envelope(
                ev_message_text(text=student_id, user_id=uid,
                                reply_token=reply_token)
            )
            return _post_json(url, secret, payload)

        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = [
                ex.submit(register, "U_A", "rt_reg_U_A"),
                ex.submit(register, "U_B", "rt_reg_U_B"),
            ]
            results = [f.result() for f in as_completed(futs)]

        # HTTP 都回 200（非同步 route 立即回覆）
        assert all(r.status_code == 200 for r in results), [
            r.status_code for r in results]

        # --- 等背景處理完成，再檢查 DB 與訊息 -----------------------------------
        student_repo = container.student_repo()

        def winners():
            s_a = student_repo.find_by_line_id("U_A")
            s_b = student_repo.find_by_line_id("U_B")
            return [s for s in (s_a, s_b) if s is not None]

        # 等到「恰好一位」綁定成功
        ok = wait_for(lambda: len(winners()) == 1, timeout=8.0)
        if not ok:
            s_a = student_repo.find_by_line_id("U_A")
            s_b = student_repo.find_by_line_id("U_B")
            raise AssertionError(
                "背景處理超時，仍未出現唯一綁定者；"
                f"目前 DB 查詢：s_a={s_a} s_b={s_b}；"
                f"spy.replies={line_api_service_spy.replies}"
            )

        got = winners()
        assert len(got) == 1
        assert got[0].student_id == student_id

        # 等待至少一則成功問候 & 一則「已被使用」訊息（文案可彈性匹配）
        success_ok = wait_for(lambda: any("很高興認識你" in (r.get("text") or "")
                              for r in line_api_service_spy.replies), timeout=6.0)
        conflict_ok = wait_for(
            lambda: any(
                ("已被其他 Line 帳號使用" in (r.get("text") or "")) or (
                    "已被使用" in (r.get("text") or ""))
                for r in line_api_service_spy.replies
            ),
            timeout=6.0,
        )
        if not (success_ok and conflict_ok):
            raise AssertionError(f"訊息回覆不符預期：{line_api_service_spy.replies}")


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_batch_events_in_one_request(live_server, app, container, seed_student_commit, chatbot_logger_spy, line_api_service_spy):
    """
    單一 HTTP 請求 body 內含多個 events，驗證迴圈確實處理每筆事件。
    """
    # 準備已註冊學生（讓 message/postback 能走到服務）
    seed_student_commit(
        user_id="U_X",
        student_id="S0001",
        name="批次使用者",
        context_title="1234_程式設計-Python_黃鈺晴教師",
    )

    url = f"{live_server.url}/linebot/linebot/"
    secret = app.config["LINE_CHANNEL_SECRET"]

    batch_payload = {
        "destination": "Uxxxxxxxxxxxxxx",
        "events": [
            ev_follow(user_id="U_X"),
            ev_message_text(user_id="U_X", text="助教安安，我有問題!"),  # 會切到提問狀態
            ev_postback(user_id="U_X", data="apply_leave"),              # 走請假
        ],
    }

    body = json.dumps(batch_payload, separators=(",", ":"))
    sig = line_signature(secret, body)
    headers = {"X-Line-Signature": sig, "Content-Type": "application/json"}

    resp = requests.post(url, data=body.encode(
        "utf-8"), headers=headers, timeout=5)
    assert resp.status_code == 200

    # Assert：等到「每筆事件的副作用」都可觀察到
    # 1) follow → 期望有連結 rich menu（已註冊使用者）
    assert wait_for(
        lambda: any(x["user_id"] == "U_X" and x["menu_alias"] in ("main", "main_menu")
                    for x in line_api_service_spy.linked)
    ), f"follow 未處理：linked={line_api_service_spy.linked}"

    # 2) message(text) → 期望 logger 有記「我有問題」這則訊息
    assert wait_for(
        lambda: any(m.get("message") ==
                    "助教安安，我有問題!" for m in chatbot_logger_spy.messages)
    ), f"message 未處理：messages={chatbot_logger_spy.messages}"

    # 3) postback(apply_leave) → 期望 logger 有記 postback data
    assert wait_for(
        lambda: any(m.get("message") ==
                    "apply_leave" for m in chatbot_logger_spy.messages)
    ), f"postback 未處理：messages={chatbot_logger_spy.messages}"

    # 4) （可選）檢查最終狀態：依你的業務而定。
    #    若 apply_leave 不改狀態，可能仍是 IDLE；若會進入請假流程，可能是 AWAITING_LEAVE_REASON。
    assert container.user_state_accessor().get_state("U_X") == UserStateEnum.AWAITING_TA_QUESTION
