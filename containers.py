from dependency_injector import containers, providers
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi

from infrastructure.mysql_student_repository import MySQLStudentRepository
from infrastructure.mysql_course_repository import MySQLCourseRepository
from infrastructure.postgresql_moodle_repository import PostgreSQLMoodleRepository
from infrastructure.gateways.line_api_service import LineApiService
from application.registration_service import RegistrationService


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

    # 4. Service Providers (Application)
    # The container automatically wires the dependencies together.
    registration_service = providers.Factory(
        RegistrationService,
        student_repo=student_repo,
        course_repo=course_repo,
        moodle_repo=moodle_repo,
        line_service=line_api_service
    )
    # ... add other services like LeaveService here ...
