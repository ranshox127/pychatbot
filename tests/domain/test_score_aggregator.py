# uv run -m pytest tests/domain/test_score_aggregator.py
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from domain.course import Course, CourseUnit
from domain.score import ScoreAggregator, ScoreReport
from domain.student import RoleEnum, Student, StudentStatus


def test_score_aggregator_should_return_score_report():
    # Arrange: 建立 mock repository
    mock_oj_repo = MagicMock()
    mock_summary_repo = MagicMock()

    # 模擬 OJ 題數與繳交數
    mock_oj_repo.get_exercise_number_by_contents_name.return_value = 10
    mock_oj_repo.get_exercise_summission_by_contents_name.return_value = 9
    mock_oj_repo.get_advance_number_by_contents_name.return_value = 5
    mock_oj_repo.get_advance_summission_by_contents_name.return_value = 3

    # 模擬 Summary 成績
    mock_summary_repo.get_latest_log_id.return_value = 123
    mock_summary_repo.is_log_under_review.return_value = False
    mock_summary_repo.get_score_result.return_value = 100

    # 建立學生與課程
    student = Student("U123", "s456", "m789", "小明", "AI課程",
                      RoleEnum.STUDENT, True, StudentStatus.REGISTERED)
    unit = CourseUnit("C1")
    unit.get_homework_deadlines(base_date=date(2025, 9, 11))

    course = Course("1122_程式設計-Python_黃鈺晴教師", ["anna@gmail.com"], leave_notice=1, day_of_week=3,
                    oj_contest_title="中央_1122", attendance_sheet_url="ai.com", units=[unit])

    # 建立 aggregator
    aggregator = ScoreAggregator(mock_oj_repo, mock_summary_repo)
    aggregator._get_mistake_review_value = MagicMock(return_value="100")

    # Act
    report = aggregator.aggregate(student, course, "C1")

    # Assert
    assert report == ScoreReport(
        contents_name="C1",
        oj_exercise_score="9 / 10",
        oj_advance_score="3 / 5",
        summary_score="100",
        mistake_review_score="100"
    )


@patch("domain.score.pd.read_csv")
def test_get_mistake_review_value_should_return_100(mock_read_csv):
    # 模擬 dataframe，要讓 target 欄位在第 5 欄（index=4）之後才會被比對
    df = pd.DataFrame({
        "欄1": ["x"],
        "欄2": ["x"],
        "欄3": ["x"],
        "欄4": ["x"],
        "錯誤回顧成績(C1)": [100]
    })
    df.insert(0, "id", ["s456"])  # 插入 id 為第一欄（總共6欄，C1會是第5 index=4）

    mock_read_csv.return_value = df

    aggregator = ScoreAggregator(None, None)
    result = aggregator._get_mistake_review_value("s456", "C1")
    assert result == 100
