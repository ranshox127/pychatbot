# uv run -m pytest tests/infrastructure/test_mysql_summary_repository.py

import pytest

from infrastructure.mysql_summary_repository import MySQLSummaryRepository

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def repo(test_config):
    return MySQLSummaryRepository(test_config.LINEBOT_DB_CONFIG, test_config.VERIFY_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean, verify_clean):
    yield


def test_get_latest_log_id_returns_correct_log_id(infra_seed_summary_grading_log, repo):
    student_ID = 'S123'
    context_title = '課程A'
    contents_name = 'C1'
    operation_time1 = '2025-08-01 16:00:00'
    operation_time2 = '2025-08-02 17:00:00'

    infra_seed_summary_grading_log(student_ID=student_ID,
                                   context_title=context_title,
                                   contents_name=contents_name,
                                   operation_time=operation_time1)
    infra_seed_summary_grading_log(student_ID=student_ID,
                                   context_title=context_title,
                                   contents_name=contents_name,
                                   operation_time=operation_time2)

    log_id = repo.get_latest_log_id(student_ID, context_title, contents_name)

    assert log_id == 2


def test_is_log_under_review_returns_true(infra_seed_summary_submission, repo):
    infra_seed_summary_submission(summary_gradding_log_id=42,
                                  verify_status='wait_review')

    assert repo.is_log_under_review(42) is True


def test_get_score_result_returns_100(infra_seed_summary_grading_log, repo):
    student_ID = 'S001'
    context_title = '課程V'
    contents_name = 'C2'
    operation_time = '2025-08-01 16:00:00'

    infra_seed_summary_grading_log(student_ID=student_ID,
                                   context_title=context_title,
                                   contents_name=contents_name,
                                   operation_time=operation_time)

    score = repo.get_score_result(
        student_ID, context_title, contents_name, '2025-08-02 00:00:00')

    assert score == 100


def test_get_score_result_returns_80(infra_seed_summary_grading_log, repo):
    student_ID = 'S001'
    context_title = '課程V'
    contents_name = 'C2'
    result = 0
    penalty = 1
    operation_time = '2025-08-01 16:00:00'

    infra_seed_summary_grading_log(student_ID=student_ID,
                                   context_title=context_title,
                                   contents_name=contents_name,
                                   result=result,
                                   penalty=penalty,
                                   operation_time=operation_time)

    score = repo.get_score_result(
        student_ID, context_title, contents_name, '2025-08-02 00:00:00')

    assert score == 80


def test_get_score_result_returns_0_when_no_match(infra_seed_summary_grading_log, repo):
    student_ID = 'S001'
    context_title = '課程V'
    contents_name = 'C8'
    result = 0
    penalty = -1
    operation_time = '2025-08-01 16:00:00'

    infra_seed_summary_grading_log(student_ID=student_ID,
                                   context_title=context_title,
                                   contents_name=contents_name,
                                   result=result,
                                   penalty=penalty,
                                   operation_time=operation_time)

    score = repo.get_score_result(
        student_ID, context_title, contents_name, '2025-08-02 00:00:00')

    assert score == 0
