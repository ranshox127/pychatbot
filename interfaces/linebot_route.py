# interfaces/linebot_route.py
from dependency_injector.wiring import Provide, inject
from flask import Blueprint, abort, current_app, request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (FollowEvent, MessageEvent, PostbackEvent,
                                 TextMessageContent)

# Import service classes just for type hinting
from application.registration_service import RegistrationService
from application.user_state_accessor import UserStateAccessor
from application.ask_TA_service import AskTAService
from application.leave_service import LeaveService
from application.check_attendance_service import CheckAttendanceService
from application.check_score_service import CheckScoreService
from application.chatbot_logger import ChatbotLogger
from domain.student import StudentRepository
from domain.user_state import UserStateEnum
from containers import AppContainer

# command_handlers = {
#     "助教安安，我有問題!": handle_student_help,
#     "我要請假": student_ask_for_leave,
#     "give_me_postback": get_postback
# }


@inject
def handle_follow(
    event: FollowEvent,
    destination: str,                # 👈 第二個位置參數用來接住 line-bot-sdk 傳進來的 destination
    *,
    registration_service: RegistrationService = Provide[AppContainer.registration_service]
):
    user_id = event.source.user_id
    registration_service.handle_follow_event(user_id, event.reply_token)


@inject
def handle_message(
    event: MessageEvent,
    destination: str,                # 👈 第二個位置參數用來接住 line-bot-sdk 傳進來的 destination
    *,
    student_repository: StudentRepository = Provide[AppContainer.student_repo],
    registration_service: RegistrationService = Provide[AppContainer.registration_service],
    user_state_accessor: UserStateAccessor = Provide[AppContainer.user_state_accessor],
    ask_ta_service: AskTAService = Provide[AppContainer.ask_ta_service],
    check_score_service: CheckScoreService = Provide[AppContainer.check_score_service],
    leave_service: LeaveService = Provide[AppContainer.leave_service],
    chatbot_logger: ChatbotLogger = Provide[AppContainer.chatbot_logger]
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

    session_state = user_state_accessor.get_state(user_id).status

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
            student=student, reply_token=event.reply_token, target_content=text, message_log_id=message_log_id)
    elif session_state == UserStateEnum.AWAITING_REGRADE_BY_TA_REASON:
        pass

    # 如果使用者並沒有在上述狀態進行特定的動作，則根據「指令」處理
    if text == "助教安安，我有問題!":
        ask_ta_service.start_inquiry(
            student=student, reply_token=event.reply_token)
    else:
        pass


@inject
def handle_postback(
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


def create_linebot_blueprint(container: AppContainer) -> Blueprint:
    """
    建立、組裝並設定 Linebot 的 Flask Blueprint。
    """
    linebot_bp = Blueprint('linebot', __name__, url_prefix='/linebot')

    channel_secret = container.config.LINE_CHANNEL_SECRET()
    handler = WebhookHandler(channel_secret)

    # 手動註冊已經在模組層級定義好的、且被 @inject 修補過的函式
    handler.add(FollowEvent)(handle_follow)
    handler.add(MessageEvent, message=TextMessageContent)(handle_message)
    handler.add(PostbackEvent)(handle_postback)

    @linebot_bp.route('/linebot/', methods=['POST'])
    def linebot():
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)
        current_app.logger.info("Request body: " + body)
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            current_app.logger.warning("Invalid signature.")
            abort(400)
        return 'OK'

    return linebot_bp
