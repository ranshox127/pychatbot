from typing import List
from linebot.v3.messaging import (
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    Message
)


class LineApiService:
    """
    封裝 LINE Messaging API 的 gateway。
    專注於『怎麼傳』，不處理『傳什麼』與『為什麼傳』。
    """

    def __init__(self, line_bot_api: MessagingApi):
        self.line_bot_api = line_bot_api

    def reply_message(self, reply_token: str, messages: List[Message]):
        if not isinstance(messages, list):
            messages = [messages]

        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=messages
            )
        )

    def push_message(self, user_id: str, messages: List[Message]):
        if not isinstance(messages, list):
            messages = [messages]

        self.line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=messages
            )
        )

    def switch_rich_menu_for_user(self, user_id: str, main_menu_id: str, main_menu_image_path: str):
        # main_menu_test_rich_menu_id = "richmenu-2098cb2a534de65d2d1138b9210dbffe"
        # main_menu_test_image_path = '/root/pychatbot/test_img/main_menu_test.png'

        headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
                   "Content-Type": 'application/json'}
        with open(main_menu_image_path, 'rb') as f:
            response = requests.post(
                f'https://api.line.me/v2/bot/user/{user_id}/richmenu/{main_menu_id}',
                headers=headers,
                data=f
            )
