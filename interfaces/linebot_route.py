# interfaces/linebot_route.py
import atexit
import base64
import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, abort, current_app, request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (FollowEvent, MessageEvent, PostbackEvent,
                                 TextMessageContent)

from application.ask_TA_service import AskTAService
from application.chatbot_logger import ChatbotLogger
from application.check_attendance_service import CheckAttendanceService
from application.check_score_service import CheckScoreService
from application.leave_service import LeaveService
# Import service classes just for type hinting
from application.registration_service import RegistrationService
from application.user_state_accessor import UserStateAccessor
from containers import AppContainer
from domain.student import StudentRepository
from domain.user_state import UserStateEnum

# command_handlers = {
#     "助教安安，我有問題!": handle_student_help,
#     "我要請假": student_ask_for_leave,
#     "give_me_postback": get_postback
# }


_EXECUTOR = None


@inject
def on_follow(
    event: FollowEvent,
    destination: str,                # 👈 第二個位置參數用來接住 line-bot-sdk 傳進來的 destination
    *,
    registration_service: RegistrationService = Provide[AppContainer.registration_service]
):
    user_id = event.source.user_id
    registration_service.handle_follow_event(user_id, event.reply_token)


@inject
def on_message(
    event: MessageEvent,
    destination: str,                # 👈 第二個位置參數用來接住 line-bot-sdk 傳進來的 destination
    *,
    student_repository: StudentRepository = Provide[AppContainer.student_repo],
    registration_service: RegistrationService = Provide[AppContainer.registration_service],
    user_state_accessor: UserStateAccessor = Provide[AppContainer.user_state_accessor],
    ask_ta_service: AskTAService = Provide[AppContainer.ask_ta_service],
    check_score_service: CheckScoreService = Provide[AppContainer.check_score_service],
    leave_service: LeaveService = Provide[AppContainer.leave_service],
    chatbot_logger: ChatbotLogger = Provide[AppContainer.chatbot_logger],
    mistake_review_sheet_url: str = Provide[AppContainer.config.MISTAKE_REVIEW_SHEET_URL]
):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 第一層：存在性檢查
    student = student_repository.find_by_line_id(user_id)
    if not student:
        # 如果使用者不存在，任何訊息都視為嘗試註冊學號
        registration_service.register_student(
            user_id, text, event.reply_token)
        return

    # 第二層：領域狀態檢查 (雖然在目前流程中，不存在的用戶已處理，但這是一個好的實踐)
    if not student.is_registered():
        registration_service.register_student(
            user_id, text, event.reply_token)
        return

    # 第三層：對話狀態檢查
    message_log_id = chatbot_logger.log_message(
        student_id=student.student_id, message=text, context_title=student.context_title)

    session_state = user_state_accessor.get_state(user_id)

    if session_state == UserStateEnum.AWAITING_LEAVE_REASON:
        leave_service.submit_leave_reason(
            student=student, reason=text, reply_token=event.reply_token)
        return
    elif session_state == UserStateEnum.AWAITING_TA_QUESTION:
        ask_ta_service.submit_question(
            student=student, message_log_id=message_log_id)
        return
    elif session_state == UserStateEnum.AWAITING_CONTENTS_NAME:
        check_score_service.check_score(
            student=student, reply_token=event.reply_token, target_content=text, mistake_review_sheet_url=mistake_review_sheet_url, message_log_id=message_log_id)
    elif session_state == UserStateEnum.AWAITING_REGRADE_BY_TA_REASON:
        pass

    # 如果使用者並沒有在上述狀態進行特定的動作，則根據「指令」處理
    if text == "助教安安，我有問題!":
        ask_ta_service.start_inquiry(
            student=student, reply_token=event.reply_token)
    else:
        pass


@inject
def on_postback(
    event: PostbackEvent,
    destination: str,                # 👈 第二個位置參數用來接住 line-bot-sdk 傳進來的 destination
    *,
    student_repository: StudentRepository = Provide[AppContainer.student_repo],
    check_attendance_service: CheckAttendanceService = Provide[
        AppContainer.check_attendance_service],
    check_score_service: CheckScoreService = Provide[AppContainer.check_score_service],
    user_state_accessor: UserStateAccessor = Provide[AppContainer.user_state_accessor],
    leave_service: LeaveService = Provide[AppContainer.leave_service],
    chatbot_logger: ChatbotLogger = Provide[AppContainer.chatbot_logger]
):
    """
    main menu:
    + 請假按鈕
    + 查詢出席
    + 查詢成績

    請假:
    + 是
    + 否

    總結評分表單:
    + 取得分數
    + 重新評分
    + 人工評分

    總結人工評分:
    + 是
    + 否

    """
    user_id = event.source.user_id

    student = student_repository.find_by_line_id(user_id)

    postback_action = event.postback.data

    message_log_id = chatbot_logger.log_message(
        student_id=student.student_id, message=postback_action, context_title=student.context_title)

    if postback_action == 'apply_leave':
        leave_service.apply_for_leave(
            student=student, reply_token=event.reply_token)

    elif postback_action == 'fetch_absence_info':
        check_attendance_service.check_attendance(
            student=student, reply_token=event.reply_token)

    elif postback_action == 'check_homework':
        check_score_service.check_publish_contents(
            student=student, reply_token=event.reply_token)

    elif postback_action == '[Action]confirm_to_leave':
        leave_service.ask_leave_reason(
            student=student, reply_token=event.reply_token, message_log_id=message_log_id)

    elif postback_action == '[Action]cancel_to_leave':
        user_state_accessor.set_state(
            student.line_user_id, UserStateEnum.IDLE)

    elif postback_action == '[INFO]get_summary_grading':
        pass
    elif postback_action == '[INFO]summary_re-gradding':
        pass
    elif postback_action == '[INFO]summary_re-gradding_by_TA':
        pass
    elif postback_action == '[INFO]summary_re-gradding_by_TA_check':
        pass


# 2) 自己的 dispatcher，把 parser 解析出來的 event 送到對應處理器
def _dispatch(event, destination: str):
    if isinstance(event, FollowEvent):
        return on_follow(event, destination)
    if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
        return on_message(event, destination)
    if isinstance(event, PostbackEvent):
        return on_postback(event, destination)
    # 其他 event 類型略過

    return


# 3) blueprint 工廠：只負責「用真 secret 替換 parser」+ 解析/派發
def _valid_signature(secret: str, body: str, sig: str | None) -> bool:
    if not sig:
        return False
    mac = hmac.new(secret.encode("utf-8"), body.encode("utf-8"),
                   hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(sig, expected)


def _get_executor(app):
    global _EXECUTOR
    if _EXECUTOR is None:
        workers = int(app.config.get("LINE_EXECUTOR_WORKERS", 4))
        _EXECUTOR = ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="linebot-bg")
        atexit.register(lambda: _EXECUTOR and _EXECUTOR.shutdown(
            wait=False, cancel_futures=True))
        app.logger.info("LINE executor started (workers=%s)", workers)
    return _EXECUTOR


# ✅ 背景執行緒內「用 SDK 解析出事件物件」，再交給 _dispatch
def _process_payload_in_bg(app, body: str, signature: str):
    with app.app_context():
        try:
            # 用真 secret 建 parser（避免全域 parser 秘密不同步）
            parser = WebhookParser(app.config["LINE_CHANNEL_SECRET"])
            # ← 產生 FollowEvent / MessageEvent / PostbackEvent 物件
            events = parser.parse(body, signature)

            # 目的地在原始 body 裡，事件物件沒有這個欄位
            destination = (json.loads(body) or {}).get("destination", "")

            app.logger.info("BG start: events=%d", len(events))
            for ev in events:
                # ← 現在 isinstance 會成立，handlers 會被呼叫
                _dispatch(ev, destination)
            app.logger.info("BG done: events=%d", len(events))

        except InvalidSignatureError:
            app.logger.warning("BG invalid signature; dropped")
        except Exception as e:
            app.logger.exception("Background processing failed: %s", e)


def create_linebot_blueprint(container):
    bp = Blueprint("linebot", __name__)

    @bp.post("/linebot/linebot/")
    def webhook():
        try:
            secret = current_app.config["LINE_CHANNEL_SECRET"]
            body = request.get_data(as_text=True)
            sig = request.headers.get("X-Line-Signature")

            if not _valid_signature(secret, body, sig):
                current_app.logger.warning("Invalid signature")
                abort(400)

            ex = _get_executor(current_app._get_current_object())
            current_app.logger.info("SUBMIT payload len=%d", len(body))
            # ✅ 把 signature 一起傳進背景，讓 parser.parse 使用
            ex.submit(_process_payload_in_bg,
                      current_app._get_current_object(), body, sig)
            return "", 200

        except Exception as e:
            current_app.logger.exception("webhook failed: %s", e)
            # 臨時 fallback（便於過渡調試；確定穩定後可移除）
            try:
                _process_payload_in_bg(
                    current_app._get_current_object(), body, sig)
                return "", 200
            except Exception:
                return "", 500

    return bp
