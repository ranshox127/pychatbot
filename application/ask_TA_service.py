from domain.student import Student, StudentRepository
from application.user_state_accessor import UserStateAccessor
from domain.user_state import UserStateEnum
from infrastructure.gateways.line_api_service import LineApiService


class AskTAService:
    def __init__(self, student_repo: StudentRepository, user_state_accessor: UserStateAccessor, line_service: LineApiService):
        self.student_repo = student_repo
        self.user_state_accessor = user_state_accessor
        self.line_service = line_service

    def start_inquiry(self, line_user_id: str, reply_token: str):
        self.user_state_accessor.set_state(
            line_user_id, UserStateEnum.AWAITING_TA_QUESTION)
        self.line_service.reply_text_message(reply_token, "請留下問題。")

    def submit_question(self, line_user_id: str, text: str):
        student = self.student_repo.find_by_line_id(line_user_id)
        self.user_state_accessor.set_state(
            line_user_id, UserStateEnum.IDLE)
        # self.message_repo.save_message()
        # self.event_repo.save_event()
