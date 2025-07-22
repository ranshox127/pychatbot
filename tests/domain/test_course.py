"""
測試 get_next_course_date 的行為是否符合預期。

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
"""
from datetime import date, datetime
from unittest.mock import patch

import pytest

from domain.course import Course

MOCK_DATE = date(2025, 9, 25)  # 星期四
COURSE_START_HOUR = 9


@patch("domain.course.datetime")
@patch("domain.course.date")
def test_same_day_before_class(mock_date, mock_datetime):
    # 現在是 9/25（四）早上 8:30
    mock_date.today.return_value = MOCK_DATE
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
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
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
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
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        mock_datetime.now.return_value = datetime(2025, 9, 25, 9, 00)

        course = Course(
            context_title="Test Course",
            day_of_week=3,  # 星期四
            ta_emails=[], leave_notice=0, oj_contest_title="", attendance_sheet_url="", units=[]
        )
        assert course.get_next_course_date(
            start_hour=COURSE_START_HOUR) == "2025-10-02"
