# tests/fixtures/seed_commit.py
import pytest


@pytest.fixture
def seed_course_commit(linebot_mysql_truncate):
    """整合測試：插入 course 並 commit（autocommit 連線）"""
    def _seed_course(context_title="1122_程式設計-Python_黃鈺晴教師",
                     status="in_progress", reserved=""):
        with linebot_mysql_truncate.cursor() as cur:
            cur.execute(
                """
                INSERT INTO course_info (context_title, status, reserved)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  status=VALUES(status),
                  reserved=VALUES(reserved)
                """,
                (context_title, status, reserved),
            )
        return {"context_title": context_title}
    return _seed_course


@pytest.fixture
def seed_student_commit(linebot_mysql_truncate, seed_course_commit):
    """整合測試：插入 student 並 commit（會先確保 course 存在）"""
    def _seed_student(*, student_id="S12345678",
                      user_id="U_TEST_USER_ID",
                      mdl_id="12345",
                      name="旅歐文",
                      context_title="1122_程式設計-Python_黃鈺晴教師",
                      roleid=5,
                      deleted=0):
        seed_course_commit(context_title=context_title)
        with linebot_mysql_truncate.cursor() as cur:
            cur.execute(
                """
                INSERT INTO account_info
                    (student_ID, line_userID, mdl_ID, student_name, context_title, roleid, `del`)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  line_userID=VALUES(line_userID),
                  mdl_ID=VALUES(mdl_ID),
                  student_name=VALUES(student_name),
                  context_title=VALUES(context_title),
                  roleid=VALUES(roleid),
                  `del`=VALUES(`del`)
                """,
                (student_id, user_id, mdl_id, name,
                 context_title, roleid, deleted),
            )
        return {
            "student_id": student_id,
            "user_id": user_id,
            "mdl_id": mdl_id,
            "name": name,
            "context_title": context_title,
        }
    return _seed_student
