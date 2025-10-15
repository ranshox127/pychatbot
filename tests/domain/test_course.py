"""
# 測試 `get_next_course_date`

## 背景邏輯
考慮到同學會早上起來臨時生病、生理不適、心情不美麗，
我們希望在還沒開始上課（如早上 9 點前）時，請假仍算「本週的課」；
但如果已經過了上課時間，下一次上課就應該落在「下週」。

## 判斷依據

- 如果今天是上課日，且時間 < 上課起始時間 → 回傳今天
- 如果今天是上課日，且時間 ≥ 上課起始時間 → 回傳下週同一天
- 其他情況 → 回傳本週或下週的指定上課日

## 技術細節

get_next_course_date 內部依賴 date.today() 與 datetime.now() 取得現在時間，
而測試需要穩定與可預測(不然下次跑自動化就不會取得一樣的日期)，因此使用 unittest.mock.patch 來 mock 掉這些時間來源，
讓測試與真實時間脫鉤。

# 測試 `get_homework_deadlines`

沒啥好說，就是記得問 Anna 實際的 deadline。

"""
from datetime import date, datetime
from unittest.mock import patch

import pytest

from domain.course import Course, CourseUnit

MOCK_DATE = date(2025, 9, 25)  # 星期四
COURSE_START_HOUR = 9

pytestmark = pytest.mark.unit


@patch("domain.course.datetime")
@patch("domain.course.date")
def test_same_day_before_class(mock_date, mock_datetime):
    # 現在是 9/25（四）早上 8:30
    mock_date.today.return_value = MOCK_DATE
    mock_date.side_effect = date
    mock_datetime.now.return_value = datetime(2025, 9, 25, 8, 30)

    course = Course(
        context_title="Test Course",
        day_of_week=3,  # 星期四
        ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
    )
    assert course.get_next_course_date(
        start_hour=COURSE_START_HOUR) == "2025-09-25"


@patch("domain.course.datetime")
@patch("domain.course.date")
def test_same_day_after_class(mock_date, mock_datetime):
    # 現在是 9/25（四）中午 12:30
    mock_date.today.return_value = MOCK_DATE
    mock_date.side_effect = date
    mock_datetime.now.return_value = datetime(2025, 9, 25, 12, 30)

    course = Course(
        context_title="Test Course",
        day_of_week=3,  # 星期四
        ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
    )
    assert course.get_next_course_date(
        start_hour=COURSE_START_HOUR) == "2025-10-02"


def test_same_day_same_time():
    """
    這種寫法與函式參數順序無關，但多一層縮排
    """
    # 現在是 9/25（四）早上 9:00
    with patch("domain.course.date") as mock_date, \
            patch("domain.course.datetime") as mock_datetime:
        mock_date.today.return_value = MOCK_DATE
        mock_date.side_effect = date
        mock_datetime.now.return_value = datetime(2025, 9, 25, 9, 00)

        course = Course(
            context_title="Test Course",
            day_of_week=3,  # 星期四
            ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
        )
        assert course.get_next_course_date(
            start_hour=COURSE_START_HOUR) == "2025-10-02"


@patch("domain.course.datetime")
@patch("domain.course.date")
def test_non_class_day_should_return_nearest_future_class_day(mock_date, mock_datetime):
    # 現在是 9/25（四）中午 12:30
    mock_date.today.return_value = MOCK_DATE
    mock_date.side_effect = date
    mock_datetime.now.return_value = datetime(2025, 9, 25, 12, 30)

    course = Course(
        context_title="Test Course",
        day_of_week=4,  # 星期五
        ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
    )
    assert course.get_next_course_date(
        start_hour=COURSE_START_HOUR) == "2025-09-26"


@patch("domain.course.datetime")
@patch("domain.course.date")
def test_edge_case_cross_year(mock_date, mock_datetime):
    # 現在是 12/26（四）晚上 11:37
    mock_date.today.return_value = date(2024, 12, 26)  # 星期四
    mock_date.side_effect = date
    mock_datetime.now.return_value = datetime(2024, 12, 26, 23, 37)

    course = Course(
        context_title="Test Course",
        day_of_week=3,  # 星期四
        ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
    )
    assert course.get_next_course_date(
        start_hour=COURSE_START_HOUR) == "2025-01-02"


def test_homework_deadlines_should_return_correct_datetime_strings():
    base_date = date(2025, 9, 11)  # 星期四

    unit = CourseUnit(name="C1", deadlines=None)

    unit.get_homework_deadlines(base_date)

    assert unit.deadlines.oj_deadline == "2025-09-17 04:01:00"
    assert unit.deadlines.summary_deadline == "2025-09-18 12:01:00"


def test_homework_deadlines_cross_year():
    base_date = date(2025, 12, 18)  # 星期四

    OJ_D1 = 13
    SUMMARY_D1 = 14

    unit = CourseUnit(name="C8")

    unit.get_homework_deadlines(base_date, oj_d1=OJ_D1, summary_d1=SUMMARY_D1)

    assert unit.deadlines.oj_deadline == "2025-12-31 04:01:00"
    assert unit.deadlines.summary_deadline == "2026-01-01 12:01:00"
