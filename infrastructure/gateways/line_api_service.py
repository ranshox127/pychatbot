# infrastructure/gateways/line_api_service.py
from typing import List

import requests
from linebot.v3.messaging import (Message, MessagingApi, PushMessageRequest,
                                  ReplyMessageRequest, TextMessage)


class LineApiService:
    """
    封裝 LINE Messaging API 的 gateway。
    專注於『怎麼傳』，不處理『傳什麼』與『為什麼傳』。
    """

    def __init__(self, line_bot_api: MessagingApi, channel_access_token: str, line_rich_menus: dict):
        self.line_bot_api = line_bot_api
        self.channel_access_token = channel_access_token
        self.line_rich_menus = line_rich_menus

    def reply_message(self, reply_token: str, messages: List[Message]):
        if not isinstance(messages, list):
            messages = [messages]

        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=messages
            )
        )

    def reply_text_message(self, reply_token: str, text: str):
        """
        用簡單的文字回覆訊息。
        這個方法內部將文字轉換成 TextMessage 物件，然後呼叫核心的 reply_message。
        """
        text_message = TextMessage(text=text)
        self.reply_message(reply_token, [text_message])

    def push_message(self, user_id: str, messages: List[Message]):
        if not isinstance(messages, list):
            messages = [messages]

        self.line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=messages
            )
        )

    def link_rich_menu_to_user(self, user_id: str, menu_alias: str):
        """
        將一個預先建立好的 Rich Menu 連結給指定使用者。
        menu_alias 是一個好記的別名，例如 'main_menu' 或 'registration_menu'。
        """
        # main_menu_test_rich_menu_id = "richmenu-2098cb2a534de65d2d1138b9210dbffe"
        # main_menu_test_image_path = '/root/pychatbot/test_img/main_menu_test.png'

        rich_menu_id = self.line_rich_menus.get(menu_alias)
        if not rich_menu_id:
            print(f"[ERROR] No rich menu ID found for alias '{menu_alias}'")
            return

        url = f"https://api.line.me/v2/bot/user/{user_id}/richmenu/{rich_menu_id}"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}"
        }

        response = requests.post(url, headers=headers)
        if response.status_code != 200:
            print(
                f"[ERROR] Failed to link rich menu: {response.status_code} {response.text}")
        else:
            print(
                f"[INFO] Successfully linked rich menu '{menu_alias}' to user '{user_id}'")


class LineApiError(Exception):
    def __init__(self, status_code, response_text):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"LINE API error: {status_code} {response_text}")
