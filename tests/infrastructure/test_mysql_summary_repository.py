# uv run -m pytest tests/infrastructure/test_mysql_summary_repository.py

import pytest

from infrastructure.mysql_summary_repository import MySQLSummaryRepository


@pytest.fixture
def repo(test_config):
    return MySQLSummaryRepository(test_config.LINEBOT_DB_CONFIG, test_config.VERIFY_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean, verify_clean):
    yield

def test_get_latest_log_id_returns_correct_log_id(linebot_clean, repo):
    with linebot_clean.cursor() as cur:
        cur.execute("""
            INSERT INTO summary_gradding_log (log_id, student_ID, context_title, contents_name, operation_time)
            VALUES 
                (1, 'S123', '課程A', 'C1_Review', '2025-08-01 10:00:00'),
                (2, 'S123', '課程A', 'C1_Review', '2025-08-02 10:00:00')
        """)

    log_id = repo.get_latest_log_id('S123', '課程A', 'C1_Review')
    assert log_id == 2


def test_is_log_under_review_returns_true(verify_clean, repo):
    with verify_clean.cursor() as cur:
        cur.execute("""
            INSERT INTO SummarySubmissions (summary_gradding_log_id, verify_status)
            VALUES (42, 'wait_review')
        """)

    assert repo.is_log_under_review(42) is True


def test_get_score_result_returns_100(linebot_clean, repo):
    with linebot_clean.cursor() as cur:
        cur.execute("""
            INSERT INTO summary_gradding_log (student_ID, context_title, contents_name, result, penalty, operation_time)
            VALUES ('S001', '課程X', 'C2', 1, 0, '2025-08-01 10:00:00')
        """)

    score = repo.get_score_result('S001', '課程X', 'C2', '2025-08-02 00:00:00')
    assert score == 100


def test_get_score_result_returns_80(linebot_clean, repo):
    with linebot_clean.cursor() as cur:
        cur.execute("""
            INSERT INTO summary_gradding_log (student_ID, context_title, contents_name, result, penalty, operation_time)
            VALUES ('S002', '課程Y', 'C3', 0, 1, '2025-08-01 10:00:00')
        """)

    score = repo.get_score_result('S002', '課程Y', 'C3', '2025-08-02 00:00:00')
    assert score == 80


def test_get_score_result_returns_0_when_no_match(linebot_clean, repo):
    with linebot_clean.cursor() as cur:
        cur.execute("""
            INSERT INTO summary_gradding_log (student_ID, context_title, contents_name, result, penalty, operation_time)
            VALUES ('S002', '課程Y', 'C4', 0, -1, '2025-08-01 10:00:00')
        """)
    linebot_clean.commit()

    score = repo.get_score_result('S002', '課程Y', 'C4', '2025-08-02 00:00:00')
    assert score == 0
