from application.chatbot_logger import ChatbotLogger
from application.user_state_accessor import UserStateAccessor
from domain.course import CourseRepository
from domain.event_log import EventEnum
from domain.score import ScoreAggregator, ScoreReport, ScoreAggregationFailed
from domain.student import StudentRepository
from domain.user_state import UserStateEnum
from infrastructure.gateways.line_api_service import LineApiService


class CheckScoreService:
    def __init__(self, student_repo: StudentRepository,
                 course_repo: CourseRepository,
                 user_state_accessor: UserStateAccessor,
                 score_aggregator: ScoreAggregator,
                 line_service: LineApiService,
                 chatbot_logger: ChatbotLogger
                 ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.user_state_accessor = user_state_accessor
        self.score_aggregator = score_aggregator
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger

    def check_publish_contents(self, line_user_id: str, reply_token: str):
        student = self.student_repo.find_by_line_id(line_user_id)
        course = self.course_repo.get_course_shell(student.context_title)
        course = self.course_repo.populate_units(course)

        if course.units == []:
            self.line_service.reply_text_message(
                reply_token=reply_token, text="目前還沒有任何要繳交的作業喔。")
            return

        unit_names = [unit.name for unit in course.units]
        unit_list_text = ', '.join(unit_names)

        self.line_service.reply_text_message(
            reply_token=reply_token, text=f"請輸入要查詢的單元。(ex. {unit_list_text})")

        self.user_state_accessor.set_state(
            line_user_id, UserStateEnum.AWAITING_CONTENTS_NAME)

    def check_score(self, line_user_id: str, reply_token: str, target_content: str, mistake_review_sheet_url: str, message_log_id: int):
        student = self.student_repo.find_by_line_id(line_user_id)
        course = self.course_repo.get_course_shell(student.context_title)
        course = self.course_repo.populate_units(course)

        unit_names = [unit.name for unit in course.units]

        if target_content not in unit_names:
            self.line_service.reply_text_message(
                reply_token=reply_token, text="請單元名稱不存在，請確認後再重新查詢喔。")
            return

        try:
            report = self.score_aggregator.aggregate(
                student=student, course=course, unit_name=target_content, mistake_review_sheet_url=mistake_review_sheet_url)
        except ScoreAggregationFailed:
            self.line_service.reply_text_message(
                reply_token=reply_token,
                text="很抱歉，目前系統故障，請稍後再試。"
            )
            return

        message = self._format_score_report(report)
        self.line_service.reply_text_message(
            reply_token=reply_token, text=message)

        self.user_state_accessor.set_state(line_user_id, UserStateEnum.IDLE)

        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.CHECK_HOMEWORK,
                                      message_log_id=message_log_id, problem_id=None, hw_id=target_content, context_title=student.context_title)

    def _format_score_report(self, report: ScoreReport) -> str:
        return (
            f"同學你好，以下是你的 {report.contents_name} 作業成績：\n"
            f"OJ Exercise(完成題數): {report.oj_exercise_score}\n"
            f"OJ Advance(完成題數): {report.oj_advance_score}\n"
            f"總結概念成績: {report.summary_score}\n"
            f"錯誤回顧成績: {report.mistake_review_score}"
        )
