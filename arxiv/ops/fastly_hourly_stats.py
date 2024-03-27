r"""Script to add Fastly requests to the arXiv_stats_hourly table.

It reads these from a metric at GCP.

To use this:

   cd arxiv-base
   poetry install --extras=mysql
   poetry run python arxiv/ops/fastly_hourly_stats.py config_file_example > fastly_hourly_stats.ini
   vim fastly_hourly_stats.ini  # setup configs
   export GOOGLE_APPLICATION_CREDENTIALS=~/somefile.json # needs monitoring.timeSeries.list permission
   poetry python arxiv/ops/fastly_hourly_stats.py --config-file fastly_hourly_stats.ini

This reads from a GCP metric named "arxiv-org-fastly-requests" and uses the fitler:

    resource.type="generic_node"
    logName="projects/arxiv-production/logs/fastly_log_ingest"
    ( (jsonPayload.backend =~ "_web\d+$" (jsonPayload.state = "HIT" jsonPayload.state = "HIT-CLUSTER"
    jsonPayload.state = "HIT-WAIT" jsonPayload.state = "HIT-STALE"))
    OR (jsonPayload.backend !~ "_web\d+$") )

This filter gets any fastly log line that is either
1. from a web node backend but was a cache hit
2. not from a web node backend (i.e. at GCP)

The logs are added to GCP using `arxiv/ops/fastly_log_ingest`
"""

import datetime
import sys
from typing import Tuple, MutableMapping
import click
import configparser

import google.auth
from google.cloud.monitoring_v3 import TimeInterval, Aggregation, MetricServiceClient, ListTimeSeriesRequest

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.dialects import mysql


@click.group()
def cli():
    """The CLI."""
    pass


@cli.command()
def config_file_example():
    """Print ex config file and exit."""
    print(_config_file_example)
    sys.exit(1)


@cli.command()
@click.option('--dry-run', default=False, is_flag=True)
@click.option('--verbose', default=False, is_flag=True)
@click.option("--config-file", required=True)
def last_hour(dry_run: bool, config_file: str, verbose: bool):
    """Adds request count for last clock hour.

    Ex time is 2023-11-27T19:05:00Z, the start of the interval is
    2023-11-27T18:00:00.000000000Z and the end time will be
    2023-11-27T18:59:59.999999999Z
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    config = config["DEFAULT"]
    now, start, end = _get_default_time()
    if verbose:
        print(f"Getting all requests between start time {start} and {end}")
        credentials, project_id = google.auth.default()
        if hasattr(credentials, "service_account_email"):
            print(f"Using service account: {credentials.service_account_email}")
        else:
            print("WARNING: no service account credentials.")

    count = _get_count_from_gcp_v2(config, start, end, verbose)
    _load_count_to_db(config, count, now, dry_run, verbose)


def _get_default_time() -> Tuple[datetime.datetime, str, str]:
    # Since this uses only UTC, there should be no problems with DST transitions
    now = (datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=1))
    return now, now.strftime("%Y-%m-%dT%H:00:00.000000000Z"), now.strftime("%Y-%m-%dT%H:59:59.999999999Z")


def _get_count_from_gcp_v2(config: MutableMapping, start: str, end: str, verbose: bool):
    """Gets metric for interval.

    `start` and `end` formats are like: 2023-11-27T18:00:00.000000000Z
    """
    client = MetricServiceClient()
    # noinspection PyTypeChecker
    request = ListTimeSeriesRequest(
        name="projects/" + config["gcp_project"],
        filter=F"metric.type = \"logging.googleapis.com/user/{config['gcp_metric']}\"",
        interval=TimeInterval(start_time=start, end_time=end),
        aggregation=Aggregation(
            alignment_period="3600s",  # 1 hour
            per_series_aligner="ALIGN_SUM"
        )
    )

    page_result = client.list_time_series(request)
    if verbose:
        print("Results from GCP metric:")
        for response in page_result:
            print(response)
        print("End of results from gcp metric.")

    points = []
    for response in page_result:
        points.extend(response.points)

    if len(points) == 0:
        print(f"No points in fastly request metric between {start} and {end}. Expected 1. May be due to no traffic to fastly.")
        sys.exit(1)

    return sum([point.value.int64_value for point in points])


def _load_count_to_db(config: MutableMapping, count: int, now: datetime.datetime, dry_run: bool = True, verbose: bool = False) -> None:
    insert = text("INSERT "
                  "INTO arXiv_stats_hourly "
                  "(ymd, hour, node_num, access_type, connections) "
                  "VALUES "
                  "(:ymd, :hour, :node_num, 'A', :connections)")
    insert = insert.bindparams(ymd=now.date().isoformat(),
                               hour=now.hour,
                               node_num=config['row_node_num'],
                               connections=count)
    if dry_run or verbose:
        print(insert.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

    if dry_run:
        print("SQL not executed due to dry_run.")
        sys.exit(1)

    engine = create_engine(config['sqlalchemy_database_uri'])
    with engine.begin() as conn:
        conn.execute(insert)


_config_file_example = """
[DEFAULT]    
# DB to write to, needs rw access to arXiv_stats_hourly
sqlalchemy_database_uri=mysql://rw_user:somepassword@db.arxiv.org:1234/arXiv

# value to put in as web node ID, using zero to indicate fastly
row_node_num=0


# Name of gcp project to read from, do not preface with "projects/"
gcp_project=arxiv-production

# Name of metric to use, do not preface with "logging.googleapis.com/user/"
gcp_metric=arxiv-org-fastly-requests
"""

if __name__ == "__main__":
    cli()
