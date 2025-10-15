# uv run -m pytest tests/infrastructure/test_mysql_course_repository.py
import pytest

from infrastructure.mysql_course_repository import MySQLCourseRepository

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def repo(test_config):
    return MySQLCourseRepository(test_config.LINEBOT_DB_CONFIG, test_config.REVIEW_SYSTEM_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean, review_clean):
    # linebot_clean / review_clean 在前後已幫你清表並提供連線
    yield


def test_get_course_shell_returns_correct_course(infra_seed_course, repo):
    # 先插入測試資料
    infra_seed_course(context_title="1122_測試課程", mails_of_TAs="ta@example.com", day_of_week=3,
                      OJ_contest_title="contest_123", present_url="https://example.com")

    course = repo.get_course_shell("1122_測試課程")

    assert course is not None
    assert course.context_title == "1122_測試課程"
    assert course.ta_emails == ["ta@example.com"]
    assert course.leave_notice == 1
    assert course.oj_contest_title == "contest_123"
    assert course.attendance_sheet_url == "https://example.com"


def test_get_in_progress_courses_returns_list(infra_seed_course, repo):
    infra_seed_course(context_title="1122_測試課程", mails_of_TAs="ta@example.com", day_of_week=3,
                      OJ_contest_title="contest_123", present_url="https://example.com")

    courses = repo.get_in_progress_courses()

    titles = [c.context_title for c in courses]

    assert "1122_測試課程" in titles


def test_populate_units_adds_units(infra_seed_course, infra_seed_units, review_clean, linebot_clean, repo):

    infra_seed_course(context_title="1122_測試課程", mails_of_TAs="ta@example.com", day_of_week=3,
                      OJ_contest_title="contest_123", present_url="https://example.com")

    # 取得 course shell
    course = repo.get_course_shell("1122_測試課程")

    infra_seed_units(context_title="1122_測試課程",
                     units=[{
                         "contents_name": "C1",
                         "contents_id": "C1",          # 明確傳也可以
                         "context_id": 1234,           # 不傳也會自動從 "1234_..." 推 1234
                         "lesson_date": "2025-08-01 10:00:00",
                         "publish_flag": 1,
                         "oj_d1": 6,
                         "summary_d1": 7,
                     }],
                     set_deadline=True)

    enriched = repo.populate_units(course)

    assert len(enriched.units) == 1
    unit = enriched.units[0]
    assert unit.name == "C1"
    assert unit.deadlines.oj_deadline == "2025-08-07 04:01:00"
    assert unit.deadlines.summary_deadline == "2025-08-08 12:01:00"
