# domain/summary_repositories.py
from typing import List, Optional, Protocol, Dict, Any, Tuple


class GradingLogRepository(Protocol):
    # ——評分紀錄（Log）讀寫/查詢——
    def get_latest_log_id(self, stdID: str, context_title: str,
                          contents_name: str) -> Optional[int]: ...
    def get_summary_gradding_times(self, stdID: str, context_title: str,
                                   contents_name: str) -> int: ...
    # 若需要，也可加：get_last_gradding_summary(...) 但先照你現況即可


class SuggestionQueryRepository(Protocol):
    # ——產生建議所需的查詢（含「綜合視圖」）——
    def get_suggestion_info(self, student_id: str, context_title: str,
                            contents_name: str) -> Optional[Dict[str, Any]]: ...

    def get_questions(self, context_title: str,
                      contents_name: str) -> Tuple[List[str], List[str]]: ...
    def get_example_summary(self, context_title: str,
                            contents_name: str) -> Optional[str]: ...

    def check_summary_in_SummarySubmissions(self, log_id: int) -> bool: ...
    def is_log_under_review(self, log_id: int) -> bool: ...
    def use_summary_grading_log_id_get_GenAI_feedback(
        self, log_id: int) -> Optional[str]: ...


class FeedbackPushRepository(Protocol):
    # ——推播控管（避免重複推送）——
    def check_summary_feedback_push(self, stdID: str, context_title: str,
                                    contents_name: str) -> bool: ...

    def write_summary_feedback_push(self, stdID: str, context_title: str,
                                    contents_name: str) -> None: ...
