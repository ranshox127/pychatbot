# uv run -m pytest tests/domain/test_score_aggregator.py
from datetime import date
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from domain.course import Course, CourseUnit
from domain.score import ScoreAggregator, ScoreReport
from domain.student import RoleEnum, Student, StudentStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def student():
    return Student("U123", "s456", "m789", "小明", "AI課程", RoleEnum.STUDENT, True, StudentStatus.REGISTERED)


@pytest.fixture
def course():
    unit = CourseUnit("C1")
    unit.get_homework_deadlines(base_date=date(2025, 9, 11))
    return Course("1122_程式設計-Python_黃鈺晴教師", ["anna@gmail.com"], 1, 3, "中央_1122", "ai.com", units=[unit])


@pytest.fixture
def aggregator_with_mock(student, course):
    oj_repo = MagicMock()
    summary_repo = MagicMock()
    agg = ScoreAggregator(oj_repo, summary_repo)
    agg._get_mistake_review_value = MagicMock(return_value="100")
    return agg, oj_repo, summary_repo


@pytest.fixture
def valid_url():
    return "https://docs.google.com/spreadsheets/d/fake123/edit?gid=456"


@pytest.mark.parametrize("log_id, is_reviewing, score, expected", [
    (None, None, None, "沒有紀錄"),  # 學生根本沒提交 summary
    (123, True, None, "評分中"),  # 助教還沒驗證回饋
    (123, False, 100, "100"),
    (123, False, 80, "80"),
    (123, False, 0, "0"),
    (123, False, None, "發生異常，請通知助教。"),
    (123, False, -1, "發生異常，請通知助教。")
])
def test_summary_score_all_paths(log_id, is_reviewing, score, expected):
    repo = MagicMock()
    repo.get_latest_log_id.return_value = log_id
    repo.is_log_under_review.return_value = is_reviewing
    repo.get_score_result.return_value = score

    aggregator = ScoreAggregator(None, repo)
    result = aggregator._get_summary_score("課", "C1", "s456", "deadline")
    assert expected in result


@pytest.mark.parametrize("target_id, week_col, score, expected", [
    ("109201XXX", "C1", 100, 100),
    ("109201XXX", "C1", 0, 0),
    ("109201XXX", "C1", 50, "無成績"),
])
@patch("domain.score.pd.read_csv")
def test_mistake_review_score_various(mock_read_csv, target_id, week_col, score, expected, valid_url):
    df = pd.DataFrame({
        "id": ["109201XXX", "110408YYY"],
        "name": ["劉AA", "陳BB"],
        "department": ["系A", "系B"],
        "grade": [4, 4],
        "Week2 (C1)": [score, 100],
        "Week3 (C2)": [0, 100],
    })
    mock_read_csv.return_value = df

    aggregator = ScoreAggregator(None, None)
    result = aggregator._get_mistake_review_value(
        target_id, week_col, valid_url)
    assert result == expected


@patch("domain.score.pd.read_csv")
def test_mistake_review_id_not_found(mock_read_csv, valid_url):
    df = pd.DataFrame({
        "id": ["some_other_id"],
        "Week2 (C1)": [100]
    })
    mock_read_csv.return_value = df

    aggregator = ScoreAggregator(None, None)
    with pytest.raises(LookupError) as exc:
        result = aggregator._get_mistake_review_value("s456", "C1", valid_url)
    assert "COLUMN_NOT_FOUND" in str(exc.value)


@patch("domain.score.pd.read_csv")
def test_mistake_review_column_not_found(mock_read_csv, valid_url):
    df = pd.DataFrame({
        "id": ["s456"],
        "Week2 (C1)": [100]
    })
    mock_read_csv.return_value = df

    aggregator = ScoreAggregator(None, None)
    with pytest.raises(LookupError) as exc:
        result = aggregator._get_mistake_review_value("s456", "C1_", valid_url)
    assert "COLUMN_NOT_FOUND" in str(exc.value)


@patch("domain.score.pd.read_csv")
def test_mistake_review_score_should_handle_invalid_url(mock_read_csv):
    # 假設 regex 不 match，無效 URL
    aggregator = ScoreAggregator(None, None)
    with pytest.raises(ValueError) as exc:
        result = aggregator._get_mistake_review_value(
            "s456", "C1", "invalid-url")
    assert "INVALID_URL" in str(exc.value)


@patch("domain.score.pd.read_csv", side_effect=Exception("boom"))
def test_mistake_review_read_csv_exception(mock_read_csv, valid_url):
    aggregator = ScoreAggregator(None, None)
    with pytest.raises(RuntimeError) as exc:
        aggregator._get_mistake_review_value("s456", "C1", valid_url)
    assert "CSV_READ_ERROR" in str(exc.value)


def test_score_aggregator_should_return_score_report(student, course, aggregator_with_mock):
    student = student
    course = course
    aggregator, mock_oj_repo, mock_summary_repo = aggregator_with_mock

    mock_oj_repo.get_exercise_number_by_contents_name.return_value = 10
    mock_oj_repo.get_exercise_summission_by_contents_name.return_value = 9
    mock_oj_repo.get_advance_number_by_contents_name.return_value = 5
    mock_oj_repo.get_advance_summission_by_contents_name.return_value = 3

    mock_summary_repo.get_latest_log_id.return_value = 123
    mock_summary_repo.is_log_under_review.return_value = False
    mock_summary_repo.get_score_result.return_value = 100

    report = aggregator.aggregate(student, course, "C1", "fake_url")
    assert report == ScoreReport(
        contents_name="C1",
        scores={
            'OJ Exercise(完成題數)': "9 / 10",
            'OJ Advance(完成題數)': "3 / 5",
            '總結概念成績': "100",
            '錯誤回顧成績': "100"
        }
    )


def test_aggregate_should_raise_if_unit_not_found(student, course, aggregator_with_mock):
    student = student
    course = course
    aggregator, mock_oj_repo, mock_summary_repo = aggregator_with_mock

    with pytest.raises(ValueError, match="找不到單元 C1_"):
        aggregator.aggregate(student, course, "C1_", "url")

# === OJ 題數為 0 ===


def test_oj_score_should_return_divide_by_zero_safe():
    mock_oj_repo = MagicMock()
    mock_oj_repo.get_exercise_number_by_contents_name.return_value = 0
    mock_oj_repo.get_exercise_summission_by_contents_name.return_value = 9

    aggregator = ScoreAggregator(mock_oj_repo, None)
    result = aggregator._get_OJ_exercise_score(
        "oj_title", "C1", "s456", "deadline")
    assert result == "9 / 0"
