# uv run -m pytest tests/application/test_mail_carrier.py
from unittest.mock import MagicMock, patch

from application.mail_carrier import (EmailContent, GmailSMTPMailCarrier,
                                      LeaveEmailContent)
from domain.leave_request import LeaveRequest


def test_leave_email_subject_and_body():
    leave = LeaveRequest(
        operation_time="",
        student_id="114514000",
        student_name="旅歐文",
        apply_time="2025-07-22",
        reason="牙痛請假",
        context_title="1122_程式設計-Python_黃鈺晴教師"
    )

    expected_html = """
    學號: <p>$stdID</p> 姓名: <p>$name</p>
    請假日期: <p>$apply_time</p>
    請假原因: <pre>$reason</pre>
    """

    with patch("application.mail_carrier.Path.read_text", return_value=expected_html):
        email = LeaveEmailContent(leave)

        assert "[chatbot]" in email.subject()
        assert leave.context_title in email.subject()
        body = email.body()

        assert "牙痛請假" in body
        assert "旅歐文" in body
        assert "2025-07-22" in body


class DummyContent(EmailContent):
    def subject(self): return "測試主旨"
    def body(self): return "<p>測試內容</p>"


@patch("application.mail_carrier.smtplib.SMTP")
def test_gmail_smtp_send(mock_smtp_cls):
    mock_smtp = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

    mailer = GmailSMTPMailCarrier("from@gmail.com", "fakepassword")
    content = DummyContent()

    mailer.send_email(["ta@school.edu"], content)

    mock_smtp.ehlo.assert_called_once()
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("from@gmail.com", "fakepassword")
    mock_smtp.send_message.assert_called_once()

    msg = mock_smtp.send_message.call_args[0][0]
    assert msg["subject"] == "測試主旨"
    assert msg["to"] == "ta@school.edu"
    html_part = msg.get_payload()[0]
    html_decoded = html_part.get_payload(decode=True).decode()
    assert html_decoded == "<p>測試內容</p>"