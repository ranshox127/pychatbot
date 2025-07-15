from application.chatbot_logger import ChatbotLogger
from application.user_state_accessor import UserStateAccessor
from domain.event_log import EventEnum
from domain.student import StudentRepository
from domain.user_state import UserStateEnum
from infrastructure.gateways.line_api_service import LineApiService


class AskTAService:
    def __init__(self, student_repo: StudentRepository, user_state_accessor: UserStateAccessor, line_service: LineApiService, chatbot_logger: ChatbotLogger):
        self.student_repo = student_repo
        self.user_state_accessor = user_state_accessor
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger

    def start_inquiry(self, line_user_id: str, reply_token: str):
        self.user_state_accessor.set_state(
            line_user_id, UserStateEnum.AWAITING_TA_QUESTION)
        self.line_service.reply_text_message(reply_token, "請同學留下問題~助教會盡快回覆!")

    def submit_question(self, line_user_id: str, message_log_id: int):
        student = self.student_repo.find_by_line_id(line_user_id)
        self.user_state_accessor.set_state(
            line_user_id, UserStateEnum.IDLE)
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.ASK_TA_QUESTION,
                                      message_log_id=message_log_id, problem_id=None, hw_id=None, context_title=student.context_title)
