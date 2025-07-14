from dependency_injector.wiring import Provide, inject
from flask import Blueprint, abort, current_app, request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (ApiClient, ReplyMessageRequest, TextMessage)
from linebot.v3.webhooks import (FollowEvent, MessageEvent, PostbackEvent,
                                 TextMessageContent)

# Import service classes just for type hinting
from application.registration_service import RegistrationService
from application.user_state_accessor import UserStateAccessor
from application.ask_TA_service import AskTAService
from application.leave_service import LeaveService
from domain.student import StudentRepository
from domain.user_state import UserStateEnum
from containers import AppContainer

# command_handlers = {
#     "助教安安，我有問題!": handle_student_help,
#     "我要請假": student_ask_for_leave,
#     "give_me_postback": get_postback
# }


def create_linebot_blueprint() -> Blueprint:
    """
    建立並設定 Linebot 的 Flask Blueprint。
    這是一個工廠函式，確保所有依賴都在正確的 scope 內被建立。
    """
    linebot_bp = Blueprint('linebot', __name__, url_prefix='/linebot')

    # 在工廠內部，我們從 DI 容器中獲取配置來建立 handler。
    # 因為 `wire` 函式會在 app 啟動時執行，所以此處可以安全地 Provide。
    handler = WebhookHandler(Provide[AppContainer.config.LINE_CHANNEL_SECRET])

    # === 在此定義所有的路由和事件處理器 ===

    @linebot_bp.route('/linebot/', methods=['POST'])
    def linebot():
        """這是接收 LINE Webhook 的主要進入點。"""
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)
        current_app.logger.info("Request body: " + body)

        try:
            # handler 現在是定義好的，可以安全使用
            handler.handle(body, signature)
        except InvalidSignatureError:
            current_app.logger.warning("Invalid signature.")
            abort(400)
        return 'OK'

    # 因為 handler 已經在本函式 scope 內定義，
    # 所以 @handler.add 裝飾器可以正確地找到它。
    @handler.add(FollowEvent)
    @inject
    def handle_follow(
        event: FollowEvent,
        registration_service: RegistrationService = Provide[AppContainer.registration_service]
    ):
        user_id = event.source.user_id
        registration_service.handle_follow_event(user_id, event.reply_token)

    @handler.add(MessageEvent, message=TextMessageContent)
    @inject
    def handle_message(
        event: MessageEvent,
        student_repository: StudentRepository = Provide[AppContainer.student_repo],
        registration_service: RegistrationService = Provide[AppContainer.registration_service],
        user_state_accessor: UserStateAccessor = Provide[AppContainer.user_state_accessor],
        ask_ta_service: AskTAService = Provide[AppContainer.ask_ta_service],
        leave_service: LeaveService = Provide[AppContainer.leave_service]
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
        # 這裡的 is_registered() 來自 domain/student.py
        if not student.is_registered():
            # 可能處於剛加入好友但還未輸入學號的狀態
            registration_service.register_student(
                user_id, text, event.reply_token)
            return

        # 第三層：對話狀態檢查
        # 這裡的 UserStateEnum 來自 application/state_management_service.py
        session_state = user_state_accessor.get_state(user_id).status

        if session_state == UserStateEnum.AWAITING_LEAVE_REASON:
            leave_service.submit_leave_reason(
                user_id, text, event.reply_token, student)
            return
        elif session_state == UserStateEnum.AWAITING_TA_QUESTION:
            ask_ta_service.submit_question(
                user_id, text, event.reply_token, student)
            return
        elif session_state == UserStateEnum.AWAITING_CONTENTS_NAME:
            pass
        elif session_state == UserStateEnum.AWAITING_REGRADE_BY_TA_REASON:
            pass

        # 3. 如果使用者處於閒置 (IDLE) 狀態，則根據「指令」處理
        if text == "助教安安，我有問題!":
            ask_ta_service.start_inquiry(user_id, event.reply_token)
        else:
            pass

    @handler.add(PostbackEvent)
    @inject
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

    # === 路由和處理器定義結束 ===

    return linebot_bp
