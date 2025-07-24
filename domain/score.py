from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import Optional

import pandas as pd

from domain.student import Student
from domain.course import Course


@dataclass
class ScoreReport:
    contents_name: str
    scores: dict[str, str]


class OnlinejudgeRepository(ABC):
    @abstractmethod
    def get_exercise_number_by_contents_name(self, oj_contest_title: str, contents_name: str) -> int:
        pass

    @abstractmethod
    def get_exercise_summission_by_contents_name(self, oj_contest_title: str, contents_name: str, stdID: str, deadline) -> int:
        pass

    @abstractmethod
    def get_advance_number_by_contents_name(self, oj_contest_title: str, contents_name: str) -> int:
        pass

    @abstractmethod
    def get_advance_summission_by_contents_name(self, oj_contest_title: str, contents_name: str, stdID: str, deadline) -> int:
        pass


class SummaryRepository(ABC):
    @abstractmethod
    def get_latest_log_id(self, stdID: str, context_title: str,
                          contents_name: str) -> Optional[int]:
        pass

    @abstractmethod
    def is_log_under_review(self, log_id: int) -> bool:
        pass

    @abstractmethod
    def get_score_result(self, stdID: str, context_title: str,
                         contents_name: str, deadline: str) -> Optional[int]:
        pass


class ScoreAggregator:
    def __init__(self, oj_repo: OnlinejudgeRepository, summary_repo: SummaryRepository):
        self.oj_repo = oj_repo
        self.summary_repo = summary_repo

    def aggregate(self, student: Student, course: Course, unit_name: str, mistake_review_sheet_url: str) -> ScoreReport:
        unit = next(
            (unit for unit in course.units if unit.name == unit_name), None)
        if not unit:
            raise ValueError(f"找不到單元 {unit_name}")

        try:
            oj_exercise_score = self._get_OJ_exercise_score(
                stdID=student.student_id, contents_name=unit_name, oj_contest_title=course.oj_contest_title, deadline=unit.deadlines.oj_deadline
            )
            oj_advance_score = self._get_OJ_advance_score(
                stdID=student.student_id, contents_name=unit_name, oj_contest_title=course.oj_contest_title, deadline=unit.deadlines.oj_deadline
            )
            summary_score = self._get_summary_score(
                context_title=course.context_title, stdID=student.student_id, contents_name=unit_name, deadline=unit.deadlines.summary_deadline)
            mistake_review_score = self._get_mistake_review_value(
                student.student_id, unit_name, mistake_review_sheet_url)
        except Exception as e:
            error_code = getattr(e, "args", ["UNKNOWN_ERROR"])[0]
            mistake_review_score = f"發生異常，請通知助教。(異常代碼: {error_code})"

        return ScoreReport(
            contents_name=unit_name,
            scores={
                "OJ Exercise(完成題數)": oj_exercise_score,
                "OJ Advance(完成題數)": oj_advance_score,
                "總結概念成績": summary_score,
                "錯誤回顧成績": mistake_review_score
            }
        )

    def _get_OJ_exercise_score(self, oj_contest_title, contents_name, stdID, deadline) -> str:
        """
        OJ_score = math.ceil(100 * OJ_all_submission / OJ_all_problem)
        if OJ_score > 100: OJ_score = 100
        return OJ_score
        """
        OJ_all_problem = self.oj_repo.get_exercise_number_by_contents_name(
            oj_contest_title=oj_contest_title, contents_name=contents_name)

        OJ_all_submission = self.oj_repo.get_exercise_summission_by_contents_name(
            oj_contest_title=oj_contest_title, contents_name=contents_name, stdID=stdID, deadline=deadline)

        return f'{OJ_all_submission} / {OJ_all_problem}'

    def _get_OJ_advance_score(self, oj_contest_title, contents_name, stdID, deadline) -> str:
        OJ_all_problem = self.oj_repo.get_advance_number_by_contents_name(
            oj_contest_title=oj_contest_title, contents_name=contents_name)

        OJ_all_submission = self.oj_repo.get_advance_summission_by_contents_name(
            oj_contest_title=oj_contest_title, contents_name=contents_name, stdID=stdID, deadline=deadline)

        return f'{OJ_all_submission} / {OJ_all_problem}'

    def _get_summary_score(self, context_title, contents_name, stdID, deadline):
        """
        1. 取得學生提交的總結 id
        2. 是否還沒被 review
        3. 如果在 deadline 前繳交，並且 result = 1，分數為 100
        4. 如果在 deadline 前繳交，並且 result = 0、penalty != -1，分數為 80
        5. 除此之外 0 分

        ---

        根據 GPT 的建議，由於計算邏輯其實是放在資料庫的，因此分數的數字會在 repo 那邊就算好。
        這個 function 的作用是假如計算分數的邏輯又有改，就在這邊處理。
        譬如多做什麼事可加分，這個機制既不放在資料表的schema，也不放在原本的評分流程，而是真的多出來的就在這邊處理。
        """
        log_id = self.summary_repo.get_latest_log_id(
            stdID, context_title, contents_name)
        if not log_id:
            return "沒有紀錄"

        if self.summary_repo.is_log_under_review(log_id):
            return "最新提交評分中，批改完開放查詢分數，請稍候!"

        score = self.summary_repo.get_score_result(
            stdID, context_title, contents_name, deadline)
        if score == 100:
            return "100"
        elif score == 80:
            return "80"
        elif score == 0:
            return "0"
        else:
            return "發生異常，請通知助教。"

    def _get_mistake_review_value(self, stdID: str, contents_name: str, mistake_review_sheet_url: str = 'https://docs.google.com/spreadsheets/d/1izTp3WSSdTGxd3Ul65qWU3rwujLTMuE0PIP3rxllvuY/edit?gid=576676265#gid=576676265'):
        """
        查詢指定學生在某單元（週次）的錯誤回顧成績。

        此函式會從 Google Sheets 讀取學生成績數據，根據學生學號 `stdID` 與單元名稱 `contents_name`
        查找對應的錯誤回顧成績，並回傳以下幾種可能結果：

        - 0: 錯誤回顧成績為 0
        - 100: 錯誤回顧成績為 100
        - "無成績": 該欄位數值非 0 或 100，通常代表尚未完成計分

        本方法會針對常見錯誤進行例外處理，並以異常代碼拋出錯誤，例如：
        - URL 格式錯誤
        - 無法讀取 Google Sheet
        - 找不到與單元名稱對應的欄位
        - 找不到學生資料

        這些錯誤處理的目的是為了防呆，例如：助教填寫錯誤的欄位格式、提供錯誤的 Google Sheet 連結、單元命名不一致等情況。

        參數:
        - stdID (str): 學號
        - contents_name (str): 目標單元名稱（如 'C1', 'C8'）
        - mistake_review_sheet_url (str): Google Sheet 的分享連結

        回傳:
        - int: 0 或 100，代表錯誤回顧成績
        - str: "無成績"

        拋出:
        - ValueError: 當 URL 格式無效 (錯誤代碼: "INVALID_URL")
        - RuntimeError: 當 Google Sheets 無法讀取 (錯誤代碼: "CSV_READ_ERROR")
        - LookupError: 欄位或學號查無資料 (錯誤代碼: "COLUMN_NOT_FOUND" 或 "STUDENT_NOT_FOUND")

        範例:
        >>> get_mistake_review_value("jz1452896", "C1", url)
        100

        >>> get_mistake_review_value("108504510", "C8", url)
        "無成績"
        """

        sheet_id_match = re.search(
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)", mistake_review_sheet_url)
        gid_match = re.search(r"gid=([0-9]+)", mistake_review_sheet_url)

        if not (sheet_id_match and gid_match):
            raise ValueError("INVALID_URL")

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_match.group(1)}/export?format=csv&gid={gid_match.group(1)}"

        try:
            df = pd.read_csv(csv_url)
        except Exception:
            raise RuntimeError("CSV_READ_ERROR")

        # 找到包含 contents_name 的欄位
        matched_columns = [col for col in df.iloc[:,
                                                  4:].columns if f"({contents_name})" in col]

        if not matched_columns:
            raise LookupError("COLUMN_NOT_FOUND")

        value = df.loc[df['id'] == stdID, matched_columns].values

        if value.size == 0:
            raise LookupError("STUDENT_NOT_FOUND")

        if value[0][0] in (0, 100):
            return value[0][0]

        return "無成績"


class ScoreAggregationFailed(Exception):
    pass
