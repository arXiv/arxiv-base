import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from cloudevents.http import CloudEvent

from stats_functions.config import FunctionConfig, DatabaseConfig, Query

from stats_functions.utils import (
    set_up_cloud_logging,
    event_time_exceeds_retry_window,
    parse_cloud_event_time,
)


@pytest.fixture
def mock_config():
    return FunctionConfig(
        env="DEV",
        max_event_age_in_minutes=50,
        db=DatabaseConfig(
            drivername="dialect+driver",
            username="mock-user",
            password="mock-password",
            database="mock-db",
            query=Query(unix_socket="/cloudsql/mock:instance:name"),
        ),
    )


def test_set_up_cloud_logging_remote(mock_config):
    with patch("stats_functions.utils.Client") as MockCloudLoggingClient:
        mock_cloud_logging_client = MockCloudLoggingClient.return_value
        set_up_cloud_logging(mock_config)

        mock_cloud_logging_client.setup_logging.assert_called_once()


def test_set_up_cloud_logging_local(mock_config):
    mock_config.log_locally = True

    with patch("stats_functions.utils.Client") as MockCloudLoggingClient:
        set_up_cloud_logging(mock_config)
        MockCloudLoggingClient.assert_not_called()


def test_event_time_exceeds_retry_window_true(mock_config):
    mock_event_time = datetime.now(timezone.utc) - timedelta(minutes=51)

    assert event_time_exceeds_retry_window(mock_config, mock_event_time) is True


def test_event_time_exceeds_retry_window_false(mock_config):
    mock_event_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    assert event_time_exceeds_retry_window(mock_config, mock_event_time) is False


def test_parse_cloud_event_time():
    mock_attributes = {
        "type": "mock_type",
        "source": "mock_source",
        "time": "2023-10-27T12:00:00Z",
    }

    mock_cloud_event = CloudEvent(attributes=mock_attributes, data={})

    result = parse_cloud_event_time(mock_cloud_event)

    assert result.year == 2023
    assert result.month == 10
    assert result.day == 27
    assert result.tzinfo == timezone.utc
