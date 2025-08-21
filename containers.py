from dependency_injector import containers, providers
from unittest.mock import MagicMock
from linebot.v3.messaging import (
    Configuration as LineMessagingConfig,
    ApiClient,
    MessagingApi,
)

from infrastructure.mysql_student_repository import MySQLStudentRepository
from infrastructure.mysql_course_repository import MySQLCourseRepository
from infrastructure.postgresql_moodle_repository import PostgreSQLMoodleRepository
from infrastructure.mysql_event_log_repository import MySQLEventLogRepository
from infrastructure.mysql_message_log_repository import MySQLMessageLogRepository
from infrastructure.mysql_leave_repository import MySQLLeaveRepository
from infrastructure.mysql_user_state_repository import MySQLUserStateRepository
from infrastructure.postgresql_onlinejudge_repository import PostgreSQLOnlinejudgeRepository
from infrastructure.mysql_summary_repository import MySQLSummaryRepository

from infrastructure.gateways.line_api_service import LineApiService
from domain.score import ScoreAggregator
from application.registration_service import RegistrationService
from application.user_state_accessor import UserStateAccessor
from application.ask_TA_service import AskTAService
from application.check_attendance_service import CheckAttendanceService
from application.check_score_service import CheckScoreService
from application.leave_service import LeaveService
from application.chatbot_logger import ChatbotLogger
from application.mail_carrier import GmailSMTPMailCarrier


class AppContainer(containers.DeclarativeContainer):
    """
    The Dependency Injection container for the application.
    It declares how to build all our components.
    """
    # 1. Configuration Provider
    # This provider will hold the application configuration.
    config = providers.Configuration()

    # 明確產生「line-bot 的 Configuration 實例」
    line_messaging_config = providers.Factory(
        LineMessagingConfig,
        access_token=config.LINE_ACCESS_TOKEN,   # ← 確認 key 名稱真的存在
    )

    # 用上面的 Configuration 實例去建 ApiClient（單例）
    line_api_client = providers.Singleton(
        ApiClient,
        configuration=line_messaging_config,    # ← 傳 provider，會被解析成「實例」
    )

    # Real 版
    _real_line_bot_api = providers.Singleton(
        MessagingApi,
        api_client=line_api_client,
    )
    # Mock 版
    _mock_line_bot_api = providers.Singleton(
        lambda: MagicMock(spec=MessagingApi)
    )

    # 切換：容器對外只暴露 line_bot_api，一律透過這個 provider 取
    line_bot_api = providers.Selector(
        config.USE_REAL_LINE,  # bool
        **{
            True: _real_line_bot_api,
            False: _mock_line_bot_api,
        }
    )

    line_api_service = providers.Factory(
        LineApiService,
        line_bot_api=line_bot_api,                      # OK：DI 會取出實例
        channel_access_token=config.LINE_ACCESS_TOKEN,  # 供你的 gateway 需要時使用
        line_rich_menus=config.LINE_RICH_MENUS,
    )

    # 3. Repository Providers (Infrastructure)
    student_repo = providers.Factory(
        MySQLStudentRepository,
        db_config=config.LINEBOT_DB_CONFIG
    )
    course_repo = providers.Factory(
        MySQLCourseRepository,
        linebot_db_config=config.LINEBOT_DB_CONFIG,
        rs_db_config=config.REVIEW_SYSTEM_DB_CONFIG
    )
    message_repo = providers.Factory(
        MySQLMessageLogRepository,
        db_config=config.LINEBOT_DB_CONFIG
    )
    event_repo = providers.Factory(
        MySQLEventLogRepository,
        db_config=config.LINEBOT_DB_CONFIG
    )
    leave_repo = providers.Factory(
        MySQLLeaveRepository,
        db_config=config.LINEBOT_DB_CONFIG
    )
    summary_repo = providers.Factory(
        MySQLSummaryRepository,
        linebot_db_config=config.LINEBOT_DB_CONFIG,
        verify_db_config=config.VERIFY_DB_CONFIG
    )
    user_state_repo = providers.Factory(
        MySQLUserStateRepository,
        db_config=config.LINEBOT_DB_CONFIG
    )

    moodle_repo = providers.Factory(
        PostgreSQLMoodleRepository,
        db_config=config.MOODLE_DB_CONFIG,
        ssh_config=config.MOODLE_SSH_CONFIG
    )
    oj_repo = providers.Factory(
        PostgreSQLOnlinejudgeRepository,
        db_config=config.OJ_DB_CONFIG,
        ssh_config=config.OJ_SSH_CONFIG
    )

    # 4. Service Providers (Application)
    # The container automatically wires the dependencies together.
    chatbot_logger = providers.Factory(
        ChatbotLogger, message_repo=message_repo, event_repo=event_repo)

    mail_carrier = providers.Factory(
        GmailSMTPMailCarrier, send_from=config.EMAIL_SEND_FROM, password=config.EMAIL_PASSWORD)

    user_state_accessor = providers.Factory(
        UserStateAccessor, user_state_repo=user_state_repo)

    score_aggregator = providers.Factory(
        ScoreAggregator, oj_repo=oj_repo, summary_repo=summary_repo)

    registration_service = providers.Factory(
        RegistrationService,
        student_repo=student_repo,
        course_repo=course_repo,
        moodle_repo=moodle_repo,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger
    )

    leave_service = providers.Factory(
        LeaveService,
        course_repo=course_repo,
        leave_repo=leave_repo,
        user_state_accessor=user_state_accessor,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger,
        mail_carrier=mail_carrier
    )

    ask_ta_service = providers.Factory(
        AskTAService,
        user_state_accessor=user_state_accessor,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger
    )

    check_attendance_service = providers.Factory(
        CheckAttendanceService,
        course_repo=course_repo,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger
    )

    check_score_service = providers.Factory(
        CheckScoreService,
        course_repo=course_repo,
        user_state_accessor=user_state_accessor,
        score_aggregator=score_aggregator,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger
    )

    # ... add other services like LeaveService here ...
