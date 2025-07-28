# uv run -m pytest tests/application/test_check_attendance_service.py
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from application.check_attendance_service import CheckAttendanceService
from domain.event_log import EventEnum
from domain.student import RoleEnum, Student, StudentStatus


@pytest.fixture
def student():
    return Student("lineid", "114514000", "12345", "旅歐文", "1122_程式設計-Python_黃鈺晴教師", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def service():

    course_repo = MagicMock()
    line = MagicMock()
    logger = MagicMock()

    return CheckAttendanceService(course_repo, line, logger), line, logger


def test_check_attendance_integration_flow(student):
    mock_course = MagicMock()
    mock_course.attendance_sheet_url = "https://docs.google.com/spreadsheets/d/mock_sheet_id/edit#gid=123456"

    course_repo = MagicMock()
    course_repo.get_course_shell.return_value = mock_course

    line = MagicMock()
    logger = MagicMock()

    service = CheckAttendanceService(course_repo, line, logger)

    # 模擬 _get_absence_info_by_name 回傳資料（可視為假設他測試過，這裡 focus 行為）
    absence_info = {
        "id": "114514000",
        "name": "旅歐文",
        "department": "創新學院",
        "grade": 1,
        "3/6": "缺席"
    }

    service._get_absence_info_by_name = MagicMock(return_value=absence_info)
    service._to_message = MagicMock(
        return_value="旅歐文 你好，你在以下日期有缺席紀錄:\n3/6: 缺席")

    service.check_attendance(student, "reply_token")

    # 檢查 line_bot 被呼叫正確訊息
    line.reply_text_message.assert_called_once_with(
        reply_token="reply_token",
        text="旅歐文 你好，你在以下日期有缺席紀錄:\n3/6: 缺席"
    )

    # 檢查 logger 被正確記錄
    logger.log_event.assert_called_once_with(
        student_id=student.student_id,
        event_type=EventEnum.CHECK_PRESENT,
        message_log_id=-1,
        problem_id=None,
        hw_id=None,
        context_title=student.context_title
    )


# ===_extract_sheet_id_and_gid===
def test_extract_sheet_id_and_gid_from_url():
    svc = CheckAttendanceService(None, None, None)
    url = "https://docs.google.com/spreadsheets/d/abc123456/edit#gid=98765"
    sheet_id, gid = svc._extract_sheet_id_and_gid(url)

    assert sheet_id == "abc123456"
    assert gid == "98765"

# ===_get_absence_info_by_name===


@patch("application.check_attendance_service.pd.read_csv")
def test_get_absence_info_matching_name(mock_read_csv):
    df = pd.DataFrame({
        "id": ["109201XXX", "114514000", "110408YYY"],
        "name": ["劉AA", "旅歐文", "陳BB"],
        "department": ["系A", "創新學院", "系B"],
        "grade": [4, 1, 4],
        "3/6": ["", "", "缺席"],
        "3/13": ["", "", "缺席"],
        "3/20": ["", "病假", "缺席"]
    })
    mock_read_csv.return_value = df

    svc = CheckAttendanceService(None, None, None)

    # 傳入模擬的 sheet_url
    sheet_url = "https://docs.google.com/spreadsheets/d/fake_sheet_id/edit#gid=999999"

    result = svc._get_absence_info_by_name(sheet_url, "旅歐文")

    assert result is not None
    assert result["name"] == "旅歐文"
    assert result["3/20"] == "病假"


@patch("application.check_attendance_service.pd.read_csv")
def test_get_absence_info_no_matching_name(mock_read_csv):
    df = pd.DataFrame({
        "id": ["109201XXX", "114514000", "110408YYY"],
        "name": ["劉AA", "旅歐文", "陳BB"],
        "department": ["系A", "創新學院", "系B"],
        "grade": [4, 1, 4],
        "3/6": ["", "", "缺席"],
        "3/13": ["", "", "缺席"],
        "3/20": ["", "病假", "缺席"]
    })
    mock_read_csv.return_value = df

    svc = CheckAttendanceService(None, None, None)

    # 傳入模擬的 sheet_url
    sheet_url = "https://docs.google.com/spreadsheets/d/fake_sheet_id/edit#gid=999999"

    result = svc._get_absence_info_by_name(sheet_url, "鋁歐文")

    assert result is None

# ===_to_message===


def test_to_message_with_absence_records(service):
    info = {
        "id": "114514",
        "name": "小明",
        "department": "創新學院",
        "grade": 1,
        "3/6": "缺席",
        "3/13": "",
        "3/20": "病假"
    }

    svc, line, logger = service

    result = svc._to_message(info)
    assert "小明 你好，你在以下日期有缺席紀錄:" in result
    assert "3/6: 缺席" in result
    assert "3/20: 病假" in result


def test_to_message_no_absence_records(service):
    info = {
        "id": "114514",
        "name": "小明",
        "department": "創新學院",
        "grade": 1,
        "3/6": "",
        "3/13": "",
        "3/20": ""
    }

    svc, line, logger = service

    result = svc._to_message(info)
    assert result == "小明 你好，你沒有缺席紀錄。"


def test_to_message_missing_or_invalid_data(service):
    svc, line, logger = service

    assert svc._to_message(None) == "無出席紀錄，請聯絡助教確認"
    assert svc._to_message({"id": "114514"}) == "無出席紀錄，請聯絡助教確認"
