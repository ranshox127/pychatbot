# tests/fixtures/seed.py
import pytest


@pytest.fixture
def seed_course(linebot_mysql_tx):
    """建立/覆寫課程；冪等。"""
    def _seed_course(
        context_title="1122_程式設計-Python_黃鈺晴教師",
        status="in_progress",
        reserved=""
    ):
        with linebot_mysql_tx.cursor() as cur:
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
def seed_student(linebot_mysql_tx, seed_course):
    """建立/覆寫學生；會先確保對應課程存在；冪等。"""
    def _seed_student(
        *,
        student_id="114514000",
        line_user_id="lineid",
        mdl_id="12345",
        name="旅歐文",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        roleid=5,   # student
        deleted=0,  # active
    ):
        seed_course(context_title=context_title)  # 確保課程存在
        with linebot_mysql_tx.cursor() as cur:
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
                (student_id, line_user_id, mdl_id,
                 name, context_title, roleid, deleted),
            )
        return {
            "student_id": student_id,
            "line_user_id": line_user_id,
            "mdl_id": mdl_id,
            "name": name,
            "context_title": context_title,
            "roleid": roleid,
            "deleted": deleted,
        }
    return _seed_student


@pytest.fixture
def seed_user_state(linebot_mysql_tx):
    """示意 user_state seeder（如有此表）"""
    def _seed_user_state(*, line_user_id: str, state_name: str, context=None):
        with linebot_mysql_tx.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_state (line_user_id, state_name, context)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    state_name=VALUES(state_name),
                    context=VALUES(context)
                """,
                (line_user_id, state_name, context),
            )
        return {"line_user_id": line_user_id, "state_name": state_name, "context": context}
    return _seed_user_state
