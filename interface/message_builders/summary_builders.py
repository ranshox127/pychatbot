from linebot.v3.messaging import (
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    URIAction,
    Message
)

class SummaryMenuBuilder:
    """建構課堂總結評分選單"""
    def __init__(self, contents_name: str):
        self.contents_name = contents_name

    def build(self) -> Message:
        buttons_template = ButtonsTemplate(
            title='課堂總結評分',
            text=f'嗨嗨，同學如果收到 {self.contents_name} 的建議後修改完成，可以按下重新評分～',
            actions=[
                PostbackAction(label='查看評分', data=f'summary:get_grade:{self.contents_name}'),
                PostbackAction(label='重新評分', data=f'summary:re_grade:{self.contents_name}'),
                URIAction(label='前往 BookRoll', uri='https://brpt.bookroll.org.tw/login/index.php')
            ]
        )
        return TemplateMessage(
            alt_text=f'{self.contents_name} 總結評分選單',
            template=buttons_template
        )
