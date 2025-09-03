# application/summary_usecases/grade_single.py
from typing import Any, Dict

from application.suggestion_service import SuggestionService
from application.chatbot_logger import ChatbotLogger
from application.mail_carrier import MailCarrier, SummaryRegradeContent
from application.ports.grading_port import GradingPort
from domain.course import CourseRepository
from domain.event_log import EventEnum
from domain.policies import needs_genai
from domain.student import Student
from domain.summary_repositories import SuggestionQueryRepository
from infrastructure.gateways.line_api_service import LineApiService


class GradeSingleUseCase:
    def __init__(self, grading_port: GradingPort,
                 suggestion_repo: SuggestionQueryRepository,
                 course_repo: CourseRepository,
                 line_service: LineApiService,
                 mail_carrier: MailCarrier,
                 feedbacker,  # 你現有的 GenAI 回饋服務
                 suggestion_service: SuggestionService,
                 chatbot_logger: ChatbotLogger):
        self.grading_port = grading_port
        self.suggestion_repo = suggestion_repo
        self.course_repo = course_repo
        self.line_service = line_service
        self.mail_carrier = mail_carrier
        self.feedbacker = feedbacker
        self.suggestion_service = suggestion_service
        self.chatbot_logger = chatbot_logger

    def exec(self, student: Student, contents_name: str, reply_token: str, message_log_id: str) -> Dict[str, Any]:
        # 通知 TA
        try:
            emails = self.course_repo.get_course_shell(
                student.context_title).ta_emails
            self.mail_carrier.send_email(to=emails, content=SummaryRegradeContent(
                std_id=student.student_id, display_name=student.name,
                context_title=student.context_title, contents_name=contents_name
            ))
        except Exception as e:
            pass

        # 呼叫 162 做評分（入庫）
        outcome = self.grading_port.grade_single(
            student.student_id, student.context_title, contents_name)
        status = outcome.get("status")

        # 根據最新 DB 紀錄決定回覆/是否叫 GenAI
        if status == "repeat":
            text = "你目前的總結和上次評分時一樣喔，請確定有修改後再申請重新評分。"
        elif status == "no_summary":
            text = f"查無你的「{contents_name}」總結，請先繳交後再申請評分。"
        elif status == "graded":
            latest = self.suggestion_repo.get_suggestion_info(
                student.student_id, student.context_title, contents_name)
            if needs_genai(latest):
                # 送去產生回饋（非同步完成）
                try:
                    example = self.suggestion_repo.get_example_summary(
                        student.context_title, contents_name)  # 若你把它留在 summary_repo，就改那邊
                    basic = self.suggestion_service.produce(
                        student.student_id, student.context_title, contents_name)
                    self.feedbacker.get_gpt_response_for_summary(
                        student.student_id, contents_name, latest.get(
                            "result"),
                        student.context_title, example, latest.get("summary"),
                        latest.get("log_id"), basic
                    )
                except Exception as e:
                    pass
                text = f"{contents_name} 總結評分中，等評分完成會發送至聊天室!"
            else:
                text = self.suggestion_service.produce(
                    student.student_id, student.context_title, contents_name)
        else:
            text = "系統忙碌或發生錯誤，請稍後再試。"

        self.line_service.reply_text_message(
            reply_token=reply_token, text=text)
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.SUMMARY_REGRADING,
                                      message_log_id=message_log_id, problem_id=None, hw_id=None,
                                      context_title=student.context_title)
        return {"status": status, "message": text}
