import json
import os
import requests
from flask import Blueprint, request, abort, current_app
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ButtonsTemplate,
    TemplateMessage,
    PostbackAction,
    URIAction,
    MessageAction,
    ConfirmTemplate
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent, FollowEvent

from application.registration_service import RegistrationService
from domain import student_repository
from infrastructure.mysql_student_repository import MySQLStudentRepository
from infrastructure.gateways.line_api_service import LineApiService

linebot_bp = Blueprint('linebot', __name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_ACCESS_TOKEN)

line_bot_api_client = ApiClient(configuration)
line_bot_api = MessagingApi(line_bot_api_client)

db_config = {...}
student_repository = MySQLStudentRepository(db_config)
moodle_repository = MySQLMoodleRepository(...)
line_api_service = LineApiService(line_bot_api)
registration_service = RegistrationService(
    student_repository, moodle_repository, line_api_service)


command_handlers = {
    "助教安安，我有問題!": handle_student_help,
    "我要請假": student_ask_for_leave,
    "give_me_postback": get_postback
}


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


@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    registration_service.handle_follow_event(user_id, event.reply_token)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    使用者輸入文字訊息，需要判斷該訊息是否為特定的操作。
    用狀態區分是普通訊息還是操作。
    """
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 第一層：存在性檢查
    student = student_repository.find_by_line_id(user_id)
    if not student:
        # 如果使用者不存在，任何訊息都視為嘗試註冊學號
        registration_service.register_student(user_id, text, event.reply_token)
        return

    # 第二層：領域狀態檢查 (雖然在目前流程中，不存在的用戶已處理，但這是一個好的實踐)
    # 這裡的 is_registered() 來自 domain/student.py
    if not student.is_registered():
        # 可能處於剛加入好友但還未輸入學號的狀態
        registration_service.register_student(user_id, text, event.reply_token)
        return

    # 第三層：對話狀態檢查
    # 這裡的 UserStateEnum 來自 application/state_management_service.py
    session_state = state_manager.get_state(user_id)
    if session_state == UserStateEnum.AWAITING_LEAVE_REASON:
        leave_service.submit_leave_reason(
            user_id, text, event.reply_token, student)
        return
    elif session_state == UserStateEnum.AWAITING_TA_QUESTION:
        ta_service.submit_question(user_id, text, event.reply_token, student)
        return
    elif session_state == UserStateEnum.AWAITING_CONTENTS_NAME:
        pass
    elif session_state == UserStateEnum.AWAITING_RE-GRADE_BY_TA_REASON:
        pass

    # 3. 如果使用者處於閒置 (IDLE) 狀態，則根據「指令」處理
    if text == "助教安安，我有問題!":
        ta_service.start_inquiry(user_id, event.reply_token)
    else:
        pass


@handler.add(PostbackEvent)
def handle_postback(event):
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
    with ApiClient(configuration) as api_client:
        if event.postback.data == 'apply_leave':
            leave_service.apply_for_leave(user_id)
        elif event.postback.data == 'fetch_absence_info':
            attendance_service.check_attendance(user_id)
        elif event.postback.data == 'check_homework':
            pass
        elif event.postback.data == '[Action]confirm_to_leave':
            leave_service.ask_leave_reason(user_id)
        elif event.postback.data == '[Action]cancel_to_leave':
            pass
        elif event.postback.data == '[INFO]get_summary_grading':
            pass
        elif event.postback.data == '[INFO]summary_re-gradding':
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text='你剛剛點了[重新評分]')]
                )
            )
        elif event.postback.data == '[INFO]summary_re-gradding_by_TA':
            pass
        elif event.postback.data == '[INFO]summary_re-gradding_by_TA_check':
            pass
        elif event.postback.data == 'C1':
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text='C1')]
                )
            )


# U0c7a9cd93a386a6c9283843d1a1cfd77
