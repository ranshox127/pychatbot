from dependency_injector import containers, providers
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi

from infrastructure.mysql_student_repository import MySQLStudentRepository
from infrastructure.mysql_course_repository import MySQLCourseRepository
from infrastructure.postgresql_moodle_repository import PostgreSQLMoodleRepository
from infrastructure.mysql_event_log_repository import MySQLEventLogRepository
from infrastructure.mysql_message_log_repository import MySQLMessageLogRepository
from infrastructure.mysql_user_state_repository import MySQLUserStateRepository

from infrastructure.gateways.line_api_service import LineApiService
from application.registration_service import RegistrationService
from application.user_state_accessor import UserStateAccessor
from application.ask_TA_service import AskTAService
from application.leave_service import LeaveService
from application.chatbot_logger import ChatbotLogger


class AppContainer(containers.DeclarativeContainer):
    """
    The Dependency Injection container for the application.
    It declares how to build all our components.
    """
    # 1. Configuration Provider
    # This provider will hold the application configuration.
    config = providers.Configuration()

    # 2. Gateway Providers (Infrastructure)
    # The 'config' object is used here to get required values.
    line_bot_api = providers.Singleton(
        MessagingApi,
        api_client=providers.Singleton(
            ApiClient,
            configuration=providers.Singleton(
                Configuration, access_token=config.LINE_ACCESS_TOKEN
            )
        )
    )

    line_api_service = providers.Factory(
        LineApiService,
        line_bot_api=line_bot_api,
        channel_access_token=config.LINE_ACCESS_TOKEN,
        line_rich_menus=config.LINE_RICH_MENUS
    )

    # 3. Repository Providers (Infrastructure)
    student_repo = providers.Factory(
        MySQLStudentRepository,
        db_config=config.DB_CONFIG
    )
    course_repo = providers.Factory(
        MySQLCourseRepository,
        # Assume you combine configs or pass them separately
        linebot_db_config=config.DB_CONFIG,
        rs_db_config=config.DB_CONFIG
    )
    moodle_repo = providers.Factory(
        PostgreSQLMoodleRepository,
        db_config=config.DB_CONFIG,
        ssh_config=config.SSH_CONFIG
    )
    user_state_repo = providers.Factory(
        MySQLUserStateRepository, db_config=config.DB_CONFIG)
    message_repo = providers.Factory(
        MySQLMessageLogRepository, db_config=config.DB_CONFIG)
    event_repo = providers.Factory(
        MySQLEventLogRepository, db_config=config.DB_CONFIG)

    # 4. Service Providers (Application)
    # The container automatically wires the dependencies together.
    chatbot_logger = providers.Factory(
        ChatbotLogger, message_repo=message_repo, event_repo=event_repo)

    user_state_accessor = providers.Factory(
        UserStateAccessor, user_state_repo=user_state_repo)

    registration_service = providers.Factory(
        RegistrationService,
        student_repo=student_repo,
        course_repo=course_repo,
        moodle_repo=moodle_repo,
        line_service=line_api_service,
        chatbot_logger=chatbot_logger
    )

    leave_service = providers.Factory(LeaveService)

    ask_ta_service = providers.Factory(AskTAService)

    # ... add other services like LeaveService here ...
