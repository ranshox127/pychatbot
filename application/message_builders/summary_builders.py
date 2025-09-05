from linebot.v3.messaging import (
    TemplateMessage,
    ConfirmTemplate,
    ButtonsTemplate,
    PostbackAction,
    URIAction,
    Message
)

from application.message_builders.base_builder import MessageBuilder


class SummaryMenuBuilder(MessageBuilder):
    """建構課堂總結評分選單"""

    def __init__(self, contents_name: str):
        self.contents_name = contents_name

    def build(self) -> Message:
        cn = self.contents_name
        buttons_template = ButtonsTemplate(
            title='課堂總結評分',
            text=f'嗨嗨，同學如果收到 {cn} 的課堂總結改進建議後~依照建議修改並想讓TA重新評分可以按下方表單重新評分按鈕',
            actions=[
                PostbackAction(label='獲取評分資訊', data=f'summary:get_grade:{cn}'),
                PostbackAction(label='重新評分', data=f'summary:re_grade:{cn}'),
                PostbackAction(
                    label='申請人工評分', data=f'summary:apply_manual:{cn}'),
                URIAction(label='前往BookRoll複習',
                          uri='https://brpt.bookroll.org.tw/login/index.php')
            ]
        )
        return TemplateMessage(
            alt_text=f'{cn} 總結評分選單',
            template=buttons_template
        )


class ManualGradeConfirmationBuilder(MessageBuilder):
    """建構人工評分確認訊息"""

    def __init__(self, contents_name: str):
        self.contents_name = contents_name

    def build(self) -> Message:
        cn = self.contents_name
        confirm_template = ConfirmTemplate(
            text='同學你好，請問你是否確定申請人工評分呢？',
            actions=[
                PostbackAction(
                    label='是', data=f'summary:confirm_manual:{cn}'),
                PostbackAction(label='否', data='action:cancel')
            ]
        )
        return TemplateMessage(
            alt_text='人工評分申請詢問',
            template=confirm_template
        )
