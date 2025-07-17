import re

import pandas as pd

from application.chatbot_logger import ChatbotLogger
from domain.course import CourseRepository
from domain.event_log import EventEnum
from domain.student import StudentRepository
from infrastructure.gateways.line_api_service import LineApiService


class CheckAttendanceService:
    def __init__(self, student_repo: StudentRepository,
                 course_repo: CourseRepository,
                 line_service: LineApiService,
                 chatbot_logger: ChatbotLogger
                 ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger

    def check_attendance(self, line_user_id: str, reply_token: str):
        student = self.student_repo.find_by_line_id(line_user_id)
        course = self.course_repo.get_course_shell(student.context_title)

        absence_info = self._get_absence_info_by_name(
            student.name, course.attendance_sheet_url)
        absence_text = self._to_message(absence_info)

        self.line_service.reply_text_message(
            reply_token=reply_token, text=absence_text)
        self.chatbot_logger.log_event(student_id=student.student_id, event_type=EventEnum.CHECK_PRESENT,
                                      message_log_id=-1, problem_id=None, hw_id=None, context_title=student.context_title)

    def _extract_sheet_id_and_gid(self, url: str) -> tuple[str | None, str | None]:
        sheet_id_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        gid_match = re.search(r"gid=([0-9]+)", url)
        return (
            sheet_id_match.group(1) if sheet_id_match else None,
            gid_match.group(1) if gid_match else None
        )

    def _get_absence_info_by_name(self, sheet_url: str, student_name: str) -> dict | None:
        """
        從 Google Sheet 匯出的點名紀錄中，根據學生姓名查找對應的缺席資訊。

        功能說明：
        - 此方法會將 Google Sheet 的「點名表」CSV 內容讀取為資料表（DataFrame），
          並依照學生姓名（`student_name`）過濾出對應紀錄，回傳為 dictionary 格式。

        業務背景：
        - 助教會在 Google Sheet 中填寫課堂點名結果。
        - 每位學生對應一列紀錄，欄位包含 id、name、department、grade 以及數個上課日期。
        - 欠席會以「缺席」「事假」「病假」等字樣標示在對應日期欄位。

        實作細節：
        1. `sheet_url` 是 Google Sheet 網址，方法中會從中抽出 `sheet_id` 和 `gid`。
        2. 組成 csv 下載網址：
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
           可直接以 pandas 讀取：
            df = pd.read_csv(csv_url)
        3. 使用 `df[df['name'] == student_name]` 過濾對應紀錄，並回傳第一筆（若有）作為 dict。

        若需調整功能（維護建議）：
        - 若欄位名稱變更（如從 "name" 改為 "姓名"），請修改：
            `df['name']` 改為正確欄位名稱。
        - 若學生識別改為學號（如 "id"），則需同步修改過濾條件。
        - 若需回傳多筆紀錄，可改用 `df.to_dict(orient="records")` 回傳 list。

        回傳：
        - 找到紀錄則為該筆資料的 dict。
        - 找不到或錯誤發生時回傳 None。
        """
        sheet_id, gid = self._extract_sheet_id_and_gid(sheet_url)
        if not sheet_id or not gid:
            return None

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        try:
            df = pd.read_csv(csv_url)
            df.columns = df.columns.str.strip()  # 確保 column name 無空白
            filtered = df[df['name'] == student_name]
            return filtered.iloc[0].to_dict() if not filtered.empty else None
        except Exception:
            return None

    def _to_message(self, absence_info: dict | None) -> str:
        if not absence_info or "name" not in absence_info:
            return "無出席紀錄，請聯絡助教確認"

        name = absence_info["name"]
        lines = [
            f"{name} 你好，你在以下日期有缺席紀錄:"
        ]

        has_absence = False
        for date, status in absence_info.items():
            if date not in {"id", "name", "department", "grade"} and pd.notna(status):
                lines.append(f"{date}: {status}")
                has_absence = True

        if not has_absence:
            return f"{name} 你好，你沒有缺席紀錄。"

        return "\n".join(lines)
