# application/registration_service.py
from application.chatbot_logger import ChatbotLogger
from domain.student import Student, StudentRepository
from domain.moodle_enrollment import MoodleRepository
from domain.course import CourseRepository
from domain.user_state import UserState, UserStateRepository
from domain.event_log import EventEnum
from infrastructure.gateways.line_api_service import LineApiService


class RegistrationService:
    def __init__(self, student_repo: StudentRepository, course_repo: CourseRepository, moodle_repo: MoodleRepository, state_repo: UserStateRepository, line_service: LineApiService, chatbot_logger: ChatbotLogger):
        # 依賴注入！我們不關心是 MySQL 還是其他資料庫，只要它遵守 StudentRepository 的合約即可
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.moodle_repo = moodle_repo
        self.state_repo = state_repo
        self.line_service = line_service
        self.chatbot_logger = chatbot_logger

    def handle_follow_event(self, line_user_id: str, reply_token: str):
        """
        1. 如果學生不在資料庫，則傳送文字訊息，需輸入學號註冊
        2. 否則，切換到main menu。這種情況會發生大概是因為學生有註冊過，但是換了 LINE 帳號。
        """
        student = self.student_repo.find_by_line_id(line_user_id)
        if student and student.is_registered():
            self.line_service.switch_rich_menu_for_user(
                line_user_id, 'main_menu')
        else:
            self.line_service.reply_text_message(
                reply_token, "請輸入學號以成為 Pychatbot 好友。")

    def register_student(self, line_user_id: str, student_id_input: str, reply_token: str) -> None:
        """
        學生輸入學號之後:
        1. 檢查學號是否已被他人綁定
        2. 從教學平台驗證學號
        """

        # 1. 檢查學號是否已被他人綁定
        if self.student_repo.find_by_student_id(student_id_input):
            self.line_service.reply_text_message(
                reply_token, "此學號已被其他 Line 帳號使用，請洽詢助教。")

        # 2. 從教學平台驗證學號
        enrollment = self.moodle_repo.find_student_info(
            student_id_input)
        if not enrollment:
            self.line_service.reply_text_message(
                reply_token, "在教學平台上找不到這個學號，請確認後再試一次。")

        # 3.找課程
        enrollments = self.moodle_repo.find_student_enrollments(
            student_id_input)

        in_progress_titles = {
            course.context_title for course in self.course_repo.get_in_progress_courses()}

        target_enrollment = None
        for enroll in enrollments:
            if enroll.course_fullname in in_progress_titles:
                target_enrollment = enroll
                break  # 找到第一個匹配的進行中課程

        if not target_enrollment:
            self.line_service.reply_text_message(
                reply_token, "你所在的課程目前未啟用 Chatbot 服務。")

        # 4. 建立 Student 領域物件 (業務規則封裝在內)
        new_student = Student.register(
            line_user_id=line_user_id,
            student_id=student_id_input,
            mdl_id=target_enrollment.user_id,
            name=target_enrollment.fullname,
            context_title=target_enrollment.course_fullname,
            role=target_enrollment.roleid,
            is_active=True
        )

        # 5. 透過倉儲保存
        self.student_repo.save(new_student)

        # 6. 為該學生在資料表中創建欄位
        self.state_repo.save(UserState(line_user_id=line_user_id))

        # 7. 在資料庫中記錄註冊事件
        self.chatbot_logger.log_event(student_id=new_student.student_id, event_type=EventEnum.REGISTER,
                                      message_log_id=-1, problem_id=None, hw_id=None, context_title=new_student.context_title)

        # 8. 執行註冊後的動作
        self.line_service.link_rich_menu_to_user(line_user_id, 'main_menu')

        self.line_service.reply_text_message(
            reply_token, f"{new_student.name}，你好！帳號已成功綁定。")
