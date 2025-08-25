from application.chatbot_logger import ChatbotLogger
from application.mail_carrier import LeaveEmailContent, MailCarrier
from application.message_builders.leave_builders import \
    LeaveConfirmationBuilder
from application.user_state_accessor import UserStateAccessor
from domain.course import CourseRepository
from domain.event_log import EventEnum
from domain.leave_request import LeaveRequest, LeaveRequestRepository
from domain.student import Student
from domain.user_state import UserStateEnum
from infrastructure.gateways.line_api_service import LineApiService


class LeaveService:
    def __init__(self, course_repo: CourseRepository,
                 leave_repo: LeaveRequestRepository,
                 user_state_accessor: UserStateAccessor,
                 line_service: LineApiService,
                 chatbot_logger: ChatbotLogger,
                 mail_carrier: MailCarrier):
        self.course_repo = course_repo
        self.leave_repo = leave_repo
        self.user_state_accessor = user_state_accessor
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger
        self.mail_carrier = mail_carrier

    def apply_for_leave(self, student: Student, reply_token: str):
        course = self.course_repo.get_course_shell(student.context_title)
        next_course_date = course.get_next_course_date()

        message_builder = LeaveConfirmationBuilder(
            next_class_date=next_course_date)
        message_to_send = message_builder.build()
        self.line_service.reply_message(
            reply_token=reply_token, messages=[message_to_send])

    def ask_leave_reason(self, student: Student, reply_token: str, message_log_id: str):
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.ASK_FOR_LEAVE,
                                      message_log_id=message_log_id, problem_id=None, hw_id=None, context_title=student.context_title)

        self.user_state_accessor.set_state(
            student.line_user_id, UserStateEnum.AWAITING_LEAVE_REASON)

        self.line_service.reply_text_message(
            reply_token=reply_token, text=f"{student.name}，你好，收到你的請假要求了，想請問請假的原因是甚麼呢?(請在一條訊息中進行說明)")

    def submit_leave_reason(self, student: Student, reason: str, reply_token: str):
        self.user_state_accessor.set_state(
            student.line_user_id, UserStateEnum.IDLE)

        course = self.course_repo.get_course_shell(student.context_title)
        next_course_date = course.get_next_course_date()

        leave_request = LeaveRequest(
            operation_time=self._now_string(),
            student_id=student.student_id,
            student_name=student.name,
            apply_time=next_course_date,
            reason=reason,
            context_title=student.context_title
        )

        result = self.leave_repo.save_leave_request(leave_request)

        self.line_service.reply_text_message(reply_token, result)

        if course.leave_notice and result == "收到，已經幫你請好假了。":
            self.mail_carrier.send_email(
                to=course.ta_emails, content=LeaveEmailContent(leave_request))

    def _now_string(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
