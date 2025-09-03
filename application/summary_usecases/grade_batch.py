# application/summary_usecases/grade_batch.py


from application.chatbot_logger import ChatbotLogger
from application.message_builders.summary_builders import SummaryMenuBuilder
from application.ports.grading_port import GradingPort
from application.suggestion_service import SuggestionService
from domain.policies import needs_genai
from domain.student import StudentRepository
from domain.summary_repositories import (FeedbackPushRepository,
                                         SuggestionQueryRepository)
from infrastructure.gateways.line_api_service import LineApiService


class GradeBatchUseCase:
    def __init__(self, grading_port: GradingPort,
                 suggestion_repo: SuggestionQueryRepository,
                 pushes_repo: FeedbackPushRepository,
                 student_repo: StudentRepository,
                 line_service: LineApiService,
                 feedbacker,
                 suggestion_service: SuggestionService,
                 chatbot_logger: ChatbotLogger):
        self.grading_port = grading_port
        self.suggestion_repo = suggestion_repo
        self.pushes_repo = pushes_repo
        self.student_repo = student_repo
        self.line_service = line_service
        self.feedbacker = feedbacker
        self.suggestion_service = suggestion_service
        self.chatbot_logger = chatbot_logger

    def exec(self, context_title: str, contents_name: str) -> dict:
        example = self.suggestion_repo.get_example_summary(
            context_title, contents_name)
        roster = [(s.student_id, s.line_user_id)
                  for s in self.student_repo.get_all_students(context_title)]
        stats = {"graded": 0, "repeat": 0, "no_summary": 0,
                 "error": 0, "genai": 0, "pushed": 0}

        # 1) 逐一評分
        for sid, _ in roster:
            outcome = self.grading_port.grade_single(
                sid, context_title, contents_name)  # 呼叫 162
            s = outcome.get("status", "error")
            stats[s] = stats.get(s, 0) + 1

            if s == "graded":
                latest = self.suggestion_repo.get_suggestion_info(
                    sid, context_title, contents_name)
                if needs_genai(latest):
                    try:
                        basic = self.suggestion_service.produce(
                            sid, context_title, contents_name)
                        self.feedbacker.get_gpt_response_for_summary(
                            sid, contents_name, latest.get("result"),
                            context_title, example, latest.get(
                                "summary"), latest.get("log_id"), basic
                        )
                        stats["genai"] += 1
                    except Exception as e:
                        pass

        # 2) 推送菜單 + 記錄
        for sid, line_id in roster:
            if self.pushes_repo.check_summary_feedback_push(sid, context_title, contents_name):
                self.line_service.push_message(user_id=line_id, messages=[
                                               SummaryMenuBuilder(contents_name).build()])
                self.pushes_repo.write_summary_feedback_push(
                    sid, context_title, contents_name)
                stats["pushed"] += 1

        return {"status": "ok", "stats": stats}
