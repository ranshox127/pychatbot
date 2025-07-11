from linebot.v3.messaging import (
    TemplateMessage,
    ConfirmTemplate,
    PostbackAction,
    Message
)

from base_builder import MessageBuilder

class LeaveConfirmationBuilder(MessageBuilder):
    """建構請假確認訊息"""
    def __init__(self, next_class_date: str):
        self.next_class_date = next_class_date

    def build(self) -> Message:
        confirm_template = ConfirmTemplate(
            text=f'同學你好，請問你是否確定要在 {self.next_class_date} 請假？',
            actions=[
                PostbackAction(label='是', data='action:confirm_leave'),
                PostbackAction(label='否', data='action:cancel_leave')
            ]
        )
        return TemplateMessage(
            alt_text='請假確認',
            template=confirm_template
        )
