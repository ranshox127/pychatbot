# uv run -m pytest tests/infrastructure/test_mysql_course_repository.py
import pytest

from infrastructure.mysql_course_repository import MySQLCourseRepository


@pytest.fixture
def repo(test_config):
    return MySQLCourseRepository(test_config.LINEBOT_DB_CONFIG, test_config.REVIEW_SYSTEM_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_course_info(mysql_conn, rs_mysql_conn):
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE course_info")
        cur.execute("TRUNCATE TABLE change_HW_deadline")
    mysql_conn.commit()

    with rs_mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE review_publish")
    rs_mysql_conn.commit()


def test_get_course_shell_returns_correct_course(mysql_conn, repo):
    # 先插入測試資料
    with mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO course_info (
                context_title, mails_of_TAs, leave_notice, day_of_week, OJ_contest_title, present_url, status, reserved
            ) VALUES (
                '1122_測試課程', 'ta@example.com', 1, 3, 'contest_123', 'https://example.com', 'in_progress', ''
            )
        """)
    mysql_conn.commit()

    course = repo.get_course_shell("1122_測試課程")

    assert course is not None
    assert course.context_title == "1122_測試課程"
    assert course.ta_emails == ["ta@example.com"]
    assert course.leave_notice == 1
    assert course.oj_contest_title == "contest_123"
    assert course.attendance_sheet_url == "https://example.com"


def test_get_in_progress_courses_returns_list(mysql_conn, repo):
    with mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO course_info (
                context_title, mails_of_TAs, leave_notice, day_of_week, OJ_contest_title, present_url, status, reserved
            ) VALUES (
                '1122_測試課程', 'ta@example.com', 1, 2, 'contest_A', 'https://link.com', 'in_progress', ''
            )
        """)
    mysql_conn.commit()

    courses = repo.get_in_progress_courses()
    titles = [c.context_title for c in courses]

    assert "1122_測試課程" in titles


def test_populate_units_adds_units(rs_mysql_conn, mysql_conn, repo):
    with mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO course_info (
                context_title, mails_of_TAs, leave_notice, day_of_week, OJ_contest_title, present_url, status, reserved
            ) VALUES (
                '1122_測試課程', 'ta@example.com', 1, 3, 'contest_123', 'https://example.com', 'in_progress', ''
            )
        """)
    mysql_conn.commit()

    # 取得 course shell
    course = repo.get_course_shell("1122_測試課程")

    # 在 review_publish 插入單元資料（注意欄位改為 lesson_date）
    with rs_mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO review_publish (
                context_title, contents_name, lesson_date, publish_flag
            ) VALUES (
                '1122_測試課程', 'C1_變數與資料型態', '2025-08-01 10:00:00', 1
            )
        """)
    rs_mysql_conn.commit()

    # 在 change_homework_deadline 插入對應資料
    with mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO change_HW_deadline (
                context_title, contents_name, OJ_D1, Summary_D1
            ) VALUES (
                '1122_測試課程', 'C1_變數與資料型態', 6, 7
            )
        """)
    mysql_conn.commit()

    enriched = repo.populate_units(course)

    assert len(enriched.units) == 1
    unit = enriched.units[0]
    assert unit.name == "C1"
    assert unit.deadlines.oj_deadline == "2025-08-07 04:01:00"
    assert unit.deadlines.summary_deadline == "2025-08-08 12:01:00"
