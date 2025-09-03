# application/grader_client.py
from __future__ import annotations

import time
from typing import Any, Dict, Literal, Optional

import requests
from pydantic import BaseModel, Field, ValidationError

from application.chatbot_logger import ChatbotLogger
from application.mail_carrier import MailCarrier, ManualRegradeSummaryContent
from application.message_builders.summary_builders import \
    ManualGradeConfirmationBuilder
from application.user_state_accessor import UserStateAccessor
from domain.course import CourseRepository
from domain.event_log import EventEnum
from domain.student import Student
from domain.summary_repositories import GradingLogRepository, SuggestionQueryRepository
from domain.user_state import UserStateEnum
from infrastructure.gateways.line_api_service import LineApiService

Status = Literal['graded', 'repeat', 'no_summary', 'error']


class _GradeSingleResponseModel(BaseModel):
    ok: bool = Field(default=True)
    status: Status
    log_id: Optional[int] = None


class GraderClient:  # ← 這個類別現在也符合 GradingPort
    def __init__(self, base_url: str, api_key: str, line_service: LineApiService, course_repo: CourseRepository,
                 grading_logs_repo: GradingLogRepository, suggestion_repo: SuggestionQueryRepository, feedbacker, mail_carrier: MailCarrier, chatbot_logger: ChatbotLogger, user_state_accessor: UserStateAccessor,
                 timeout: float = 8.0, retries: int = 2, backoff: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

        self.line_service = line_service
        self.course_repo = course_repo
        self.grading_logs_repo = grading_logs_repo
        self.suggestion_repo = suggestion_repo
        self.feedbacker = feedbacker
        self.mail_carrier = mail_carrier
        self.user_state_accessor = user_state_accessor
        self.chatbot_logger = chatbot_logger

    def _post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json",
                   "X-API-Key": self.api_key}
        for attempt in range(self.retries + 1):
            try:
                r = requests.post(
                    url, json=json, headers=headers, timeout=self.timeout)
                if r.status_code == 200:
                    return r.json()
                raise RuntimeError(f"162 error {r.status_code}: {r.text}")
            except Exception:
                if attempt >= self.retries:
                    raise
                time.sleep(self.backoff * (2 ** attempt))
        raise RuntimeError("request failed")

    # === 實作 GradingPort ===
    def grade_single(self, student_id: str, context_title: str, contents_name: str) -> Dict[str, object]:
        """
        呼叫 162 的 /produce_summary_grading。
        穩健回傳：至少 {"status": "...", "log_id": int|None}
        """
        payload = {
            "student_id": student_id,
            "context_title": context_title,
            "contents_name": contents_name,
        }
        try:
            raw = self._post("/produce_summary_grading", payload)
        except Exception as e:
            # 降級回傳，外層可依 'error' 處理
            return {"status": "error", "log_id": None}

        # 校驗（容忍 162 回傳未含 ok）
        try:
            parsed = _GradeSingleResponseModel(**raw)
            return {"status": parsed.status, "log_id": parsed.log_id}
        except ValidationError as ve:
            # 寬鬆兜底
            return {"status": raw.get("status", "error"), "log_id": raw.get("log_id")}

    def manual_regrade_request(self, student: Student, contents_name: str, reply_token: str):
        times = self.grading_logs_repo.get_summary_gradding_times(
            student.student_id, student.context_title, contents_name)
        if times <= 3:
            self.line_service.reply_text_message(
                reply_token=reply_token, text='重新評分次數不足，需重新評分兩次後才可以申請人工評分。')
        else:
            message_to_send = ManualGradeConfirmationBuilder(contents_name).build()
            self.line_service.reply_message(
                reply_token=reply_token, messages=[message_to_send])

    def ask_manual_regrade_reason(self, student: Student, contents_name: str, reply_token: str, message_log_id: str):
        ta_emails = self.course_repo.get_course_shell(
            student.context_title).ta_emails
        self.mail_carrier.send_email(
            to=ta_emails,
            content=ManualRegradeSummaryContent(
                std_id=student.student_id,
                display_name=student.name,
                context_title=student.context_title,
                contents_name=contents_name,
                get_suggestion_info=self.suggestion_repo.get_suggestion_info))
        
        self.user_state_accessor.set_state(
            student.line_user_id, UserStateEnum.AWAITING_REGRADE_BY_TA_REASON)
        
        self.line_service.reply_text_message(
            reply_token=reply_token, text='收到，已經幫你通知助教了，請在底下打上申請的原因(ex. 某個問題明明有回答到，卻還是被問)。')
        
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.CHALLENGE_SUMMARY_GRADING,
                                      message_log_id=message_log_id, problem_id=None, hw_id=None, context_title=student.context_title)
