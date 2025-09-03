from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
import smtplib
from string import Template
from pathlib import Path
from abc import ABC, abstractmethod

from domain.leave_request import LeaveRequest


PROJECT_ROOT = Path(__file__).resolve().parent.parent

class EmailContent(ABC):
    @abstractmethod
    def subject(self) -> str:
        pass

    @abstractmethod
    def body(self) -> str:
        pass


class MailCarrier(ABC):
    @abstractmethod
    def send_email(self, to: list[str], content: EmailContent):
        pass


class LeaveEmailContent(EmailContent):
    def __init__(self, leave: LeaveRequest):
        self.leave = leave

    def subject(self) -> str:
        return f"[chatbot] {self.leave.context_title}課程 {self.leave.apply_time} 請假"

    def body(self) -> str:
        template_path = PROJECT_ROOT / "templates" / "mail_template_for_leave.html"
        template_text = template_path.read_text(encoding='utf-8')
        template = Template(template_text)
        return template.substitute({
            "stdID": self.leave.student_id,
            "name": self.leave.student_name,
            "reason": self.leave.reason,
            "apply_time": self.leave.apply_time
        })


class SummaryRegradeContent(EmailContent):
    """
    對應舊版 send_email_for_summary：
    - 主旨：[chatbot] {context_title}課程 {contents_name} summary評分申請 BY {displayName}
    - 內文：（如題）該學生申請總結評分...（舊版以 HTML 傳，這裡維持成簡單 HTML）
    """

    def __init__(self, std_id: str, display_name: str, context_title: str, contents_name: str):
        self.std_id = std_id
        self.display_name = display_name
        self.context_title = context_title
        self.contents_name = contents_name

    def subject(self) -> str:
        return f"[chatbot] {self.context_title}課程 {self.contents_name} summary評分申請 BY {self.display_name}"

    def body(self) -> str:
        text = "(如題)該學生申請總結評分\n稍後可至 SummarySubmission 網頁檢查是否需要 verify"
        # 舊版用 "html" 寄送，這裡把換行轉成 <br> 維持行為
        safe_text = html.escape(text).replace("\n", "<br>")
        return f"<p>{safe_text}</p>"


class ManualRegradeSummaryContent(EmailContent):
    """
    對應舊版 send_email_for_summary_human_evaluation：
    - 主旨：[chatbot] {context_title}課程 {contents_name} summary評分有異議 BY {displayName}
    - 內文：templates/mail_template_for_summary_human_evaluation.html
      需提供 summary_info 並做欄位格式化（loss_kw/loss_concept_kws/excess）
    """

    def __init__(
        self,
        std_id: str,
        display_name: str,
        context_title: str,
        contents_name: str,
        # Callable[[str, str, str], dict]，例如 summary_feedback.summary().get_suggestion_info
        get_suggestion_info,
    ):
        self.std_id = std_id
        self.display_name = display_name
        self.context_title = context_title
        self.contents_name = contents_name
        self._get_suggestion_info = get_suggestion_info

    def subject(self) -> str:
        return f"[chatbot] {self.context_title}課程 {self.contents_name} summary評分有異議 BY {self.display_name}"

    def body(self) -> str:
        template_path = PROJECT_ROOT / "templates" / "mail_template_for_summary_human_evaluation.html"
        template_text = template_path.read_text(encoding="utf-8")
        template = Template(template_text)

        info = self._get_suggestion_info(
            self.std_id, self.context_title, self.contents_name) or {}

        # ---- 依舊版行為做格式化（並做 escape）----
        def _fmt_list(key: str, sep: str) -> str:
            items = info.get(key) or []
            if isinstance(items, (list, tuple)):
                return sep.join(html.escape(str(x)) for x in items)
            return html.escape(str(items))

        summary_info = dict(info)  # 淺拷貝避免改到原資料
        summary_info["loss_kw"] = _fmt_list("loss_kw", ", ")
        summary_info["loss_concept_kws"] = _fmt_list("loss_concept_kws", ", ")
        summary_info["excess"] = _fmt_list("excess", "\n")
        summary_info["stdID"] = html.escape(self.std_id)

        # 補一些模板可能會用到但舊版沒寫入的欄位（安全 fallback）
        summary_info.setdefault("displayName", html.escape(self.display_name))
        summary_info.setdefault(
            "context_title", html.escape(self.context_title))
        summary_info.setdefault(
            "contents_name", html.escape(self.contents_name))

        return template.substitute(summary_info)


class GmailSMTPMailCarrier(MailCarrier):
    def __init__(self, send_from: str, password: str):
        self.send_from = send_from
        self.password = password

    def send_email(self, to: list[str], content: EmailContent):
        msg = MIMEMultipart()
        msg["subject"] = content.subject()
        msg["from"] = self.send_from
        msg["to"] = ", ".join(to)
        msg.attach(MIMEText(content.body(), "html"))

        try:
            with smtplib.SMTP(host="smtp.gmail.com", port=587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.send_from, self.password)
                smtp.send_message(msg)
                print(f"[LOG] Email sent: {content.subject()}")
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
