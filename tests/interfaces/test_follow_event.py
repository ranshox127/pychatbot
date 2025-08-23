# uv run -m pytest tests/interfaces/test_follow_event.py
import pytest
from tests.helpers import make_base_envelope, ev_follow, post_line_event


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_follow_unregistered_triggers_register_prompt(client, app, container, seed_course_commit):

    seed_course_commit(context_title="1122_程式設計-Python_黃鈺晴教師")

    payload = make_base_envelope(ev_follow(user_id="lineid"))
    service = container.line_api_service()
    api_mock = service.line_bot_api
    api_mock.reset_mock()

    # Act
    resp, _ = post_line_event(client, app, payload)
    assert resp.status_code == 200

    # Assert：應回覆註冊提示，不應綁 Rich Menu
    api_mock.link_rich_menu_id_to_user.assert_not_called()
    api_mock.reply_message.assert_called_once()
    # 檢查文字內容（可選）
    (reply_req,), _ = api_mock.reply_message.call_args
    assert reply_req.messages[0].text.startswith("請輸入學號")


@pytest.mark.usefixtures("linebot_mysql_truncate")
def test_follow_registered_links_richmenu(client, app, container, seed_student_commit):
    # Arrange：建立「已註冊」學生
    seed_student_commit(
        student_id="S12345678",
        user_id="U_TEST_USER_ID",
        name="旅歐文",
        context_title="1122_程式設計-Python_黃鈺晴教師",
    )

    payload = make_base_envelope(ev_follow(user_id="U_TEST_USER_ID"))

    # 取得被 app 使用的 gateway 與 SDK mock，先把計數歸零，避免被其他測試污染
    service = container.line_api_service()
    api_mock = service.line_bot_api
    api_mock.reset_mock()

    # Act
    resp, _ = post_line_event(client, app, payload)
    assert resp.status_code == 200

    # Assert：SDK 被正確呼叫一次，參數正確（user_id 與 rich_menu_id）
    expected_rich_menu_id = app.config["LINE_RICH_MENUS"]["main"]
    api_mock.link_rich_menu_id_to_user.assert_called_once_with("U_TEST_USER_ID", expected_rich_menu_id)

    # 並且「不應」回覆請輸入學號（已註冊不走這個分支）
    api_mock.reply_message.assert_not_called()
    api_mock.push_message.assert_not_called()  # 可選，視你的流程而定
