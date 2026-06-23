from google.cloud.logging import Client
from cloudevents.http import CloudEvent

from sqlalchemy import create_engine, Engine, URL

from datetime import datetime, timedelta, timezone
from dateutil import parser

from arxiv_functions.config import FunctionConfig, DatabaseConfig


def set_up_cloud_logging(config: FunctionConfig):
    """
    Attach a cloud logging handler to the standard logging module
    The cloud logging client is project-aware by default

    Example use:

        logger = logging.getLogger(__name__)
        set_up_cloud_logging(config)
    """
    if config.env != "TEST" and not config.log_locally:
        cloud_logging_client = Client()
        cloud_logging_client.setup_logging()


def get_engine_unix_socket(db: DatabaseConfig) -> Engine:
    """
    Initializes a unix socket connection pool for a Cloud SQL instance of MySQL
    Must be lazily loaded to allow time for the Cloud Run instance to be configured with a connection to that Cloud SQL instance
    Automatically refreshes connections before they reach the 10 minute idle timeout for instance connections to Cloud SQL

    Example use:

        engine = None
        SessionFactory = None

        @functions_framework.cloud_event
        def function(cloud_event: CloudEvent):
            global engine, SessionFactory

            if config.env != "TEST":
                if SessionFactory is None:
                    logger.info("Initializing engine and sessionmaker")
                    engine = get_engine_unix_socket(config.db)
                    SessionFactory = sessionmaker(bind=engine)

    """
    return create_engine(
        URL.create(
            drivername=db.drivername,
            username=db.username,
            password=db.password,
            database=db.database,
            query={"unix_socket": db.query.unix_socket},
        ),
        pool_recycle=300, # recycle connections older than 5 minutes
        pool_pre_ping=True, # check if a connection is alive before handing it to a session
    )


def event_time_exceeds_retry_window(
    config: FunctionConfig, event_time: datetime
) -> bool:
    """
    Helper to prevent infinite retries by dismissing event timestamps that are too old

    Example use:

        if event_time_exceeds_retry_window(config, event_time):
            raise NoRetryError
    """
    current_time = datetime.now(timezone.utc)
    max_event_age = timedelta(minutes=config.max_event_age_in_minutes)

    if (current_time - event_time) > max_event_age:
        return True
    else:
        return False


def parse_cloud_event_time(cloud_event: CloudEvent) -> datetime:
    """
    Parse the event time from a cloud event and return it as a timezone-aware datetime object
    """
    return parser.isoparse(cloud_event["time"]).replace(tzinfo=timezone.utc)
