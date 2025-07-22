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
    oj_exercise_score: str
    oj_advance_score: str
    summary_score: str
    mistake_review_score: str  # int 或 "無成績" 或 "沒有找到對應的欄位"


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

    def aggregate(self, student: Student, course: Course, unit_name: str) -> ScoreReport:
        unit = next(unit for unit in course.units if unit.name == unit_name)

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
                student.student_id, unit_name)
        except Exception as e:
            raise ScoreAggregationFailed from e

        return ScoreReport(
            contents_name=unit_name,
            oj_exercise_score=oj_exercise_score,
            oj_advance_score=oj_advance_score,
            summary_score=summary_score,
            mistake_review_score=mistake_review_score
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
            return "無法判定"

    def _get_mistake_review_value(self, stdID: str, contents_name: str):
        """
        查詢指定學生在某單元（週次）的錯誤回顧成績。

        此函式從 Google Sheets 讀取學生成績數據，根據姓名 `name` 和單元 `contents_name`
        查找對應的錯誤回顧成績，並返回三種可能的結果：
        - 0: 錯誤回顧成績為 0
        - 100: 錯誤回顧成績為 100
        - "無成績": 該欄位數值非 0 或 100，通常代表成績尚未計算完成
        - "沒有找到對應的欄位": 若找不到與 `contents_name` 對應的欄位

        參數:
        - stdID (str): 學號
        - contents_name (str): 目標單元名稱（如 'C1', 'C8'）

        回傳:
        - int: 0 或 100，代表錯誤回顧成績
        - str: "無成績" 或 "沒有找到對應的欄位"

        例外處理:
        - 若 `sheet_url` 無效，會輸出 "無效的 Google Sheets 連結"

        範例:
        >>> get_mistake_review_value("jz1452896", "C1")
        100

        >>> get_mistake_review_value("108504510", "C8")
        "無成績"

        >>> get_mistake_review_value("123456789", "C5")
        "沒有找到對應的欄位"
        """
        sheet_url = 'https://docs.google.com/spreadsheets/d/1izTp3WSSdTGxd3Ul65qWU3rwujLTMuE0PIP3rxllvuY/edit?gid=576676265#gid=576676265'

        sheet_id_match = re.search(
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        gid_match = re.search(r"gid=([0-9]+)", sheet_url)

        if not (sheet_id_match and gid_match):
            print("無效的 Google Sheets 連結")

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_match.group(1)}/export?format=csv&gid={gid_match.group(1)}"
        df = pd.read_csv(csv_url)

        # 找到包含 contents_name 的欄位
        matched_columns = [col for col in df.iloc[:,
                                                  4:].columns if f"({contents_name})" in col]

        # 回傳對應數據
        if matched_columns:
            value = df.loc[df['id'] == stdID, matched_columns].values
            if value[0][0] == 0 or value[0][0] == 100:
                return value[0][0]
            else:
                return "無成績"
        return "沒有找到對應的欄位"


class ScoreAggregationFailed(Exception):
    """在彙總成績過程中出現錯誤時丟出的例外。"""
    pass
