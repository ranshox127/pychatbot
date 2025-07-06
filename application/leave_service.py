class LeaveService:
    def __init__(self):
        pass
    
    def apply_for_leave(self, student, next_class_date):
        pass
        # 1. get the student
        # 2. get the next class date
        # 3. send the ConfirmTemplate
        
        # confirm_template = ConfirmTemplate(
        #     text='同學你好，請問你是否確定要請假?',
        #     actions=[
        #         PostbackAction(label='是', data='[Action]Ask_for_leave'),
        #         PostbackAction(label='否', data='[Action]')
        #     ]
        # )
        # template_message = TemplateMessage(
        #     alt_text='Confirm alt text',
        #     template=confirm_template
        # )

        # line_bot_api.reply_message(
        #     ReplyMessageRequest(
        #         reply_token=event.reply_token,
        #         messages=[template_message]
        #     )
        # )
        
    def ask_leave_reason(self, student):
        pass
        # 1. get the student
        # 2. change the student's state to AWAITING_LEAVE_REASON
        # 3. send the text message to the student
        
        # f'{name}，你好，收到你的請假要求了，想請問請假的原因是甚麼呢?(請在一條訊息中進行說明)'
        
    def submit_leave_reason(self, student, reason):
        pass
        # 1. get the student
        # 2. change the student's state to IDLE
        # 3. save the record to the database
        # 4. inform TAs the student's leave reason
        # 5. send a confirmation message to the student