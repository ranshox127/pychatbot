# application/summary_usecases/get_suggestion.py
from application.chatbot_logger import ChatbotLogger
from application.suggestion_service import SuggestionService
from domain.event_log import EventEnum
from domain.student import Student
from domain.summary_repositories import GradingLogRepository, SuggestionQueryRepository
from infrastructure.gateways.line_api_service import LineApiService


class GetSuggestionUseCase:
    def __init__(self,
                 grading_logs_repo: GradingLogRepository,
                 suggestion_repo: SuggestionQueryRepository,
                 suggestion_service: SuggestionService,
                 line_service: LineApiService,
                 chatbot_logger: ChatbotLogger):
        self.grading_logs_repo = grading_logs_repo
        self.suggestion_repo = suggestion_repo
        self.suggestion_service = suggestion_service
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger

    def exec(self, student: Student, contents_name: str, reply_token: str, message_log_id: str) -> dict:
        try:
            log_id = self.grading_logs_repo.get_latest_log_id(
                student.student_id, student.context_title, contents_name)
            if log_id and self.suggestion_repo.check_summary_in_SummarySubmissions(log_id):
                text = "最新提交評分中，之後批改完會傳至聊天室並開放查詢，請稍候!" \
                    if self.suggestion_repo.is_log_under_review(log_id) \
                    else (self.suggestion_repo.use_summary_grading_log_id_get_GenAI_feedback(log_id) or "查無回饋內容，請稍後再試。")
            else:
                text = self.suggestion_service.produce(
                    student.student_id, student.context_title, contents_name)
        except Exception as e:
            text = "系統忙碌或發生錯誤，請稍後再試。"

        self.line_service.reply_text_message(
            reply_token=reply_token, text=text)
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.GET_SUMMARY_GRADING,
                                      message_log_id=message_log_id, problem_id=None, hw_id=None,
                                      context_title=student.context_title)
        return {"ok": True, "message": text}
