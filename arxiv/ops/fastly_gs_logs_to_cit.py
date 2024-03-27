r"""Script to get Fastly logs from GS and move them to a local file.

To use this:

   cd arxiv-base
   poetry install
   export GOOGLE_APPLICATION_CREDENTIALS=~/somefile.json # needs read object permission on fastly log bucket
   poetry python arxiv/ops/fastly_gs_logs_to_cit.py --help
"""
import heapq
import logging
import os
import re
import tempfile
from datetime import date, timedelta
from datetime import datetime
import dateutil.parser
from pathlib import Path
from typing import Optional, List
import shutil

import google.auth
import pytz
from google.cloud import storage

import fire

logging.basicConfig()
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

TMP_DIR="/tmp"  # needs reasonable temp FS, 600MB of work space

DEFAULT_BUCKET = "arxiv-logs-archive"
DEFAULT_KEY = "site/fastly/" + datetime.utcnow().strftime("%Y/fastly_access_log.%Y-%m-%dT%H")

# Since fastly logs are UTC we need UTC times to handle fastly filenames
UTC_PREVIOUS_HOUR = (datetime.now().replace(minute=00, microsecond=0, second=0) - timedelta(hours=1)).astimezone(pytz.timezone("UTC"))

ET_TZ = tzinfo=pytz.timezone("US/Eastern")

# Since arXiv logs are stored with ET, need the ET year
_et_year = UTC_PREVIOUS_HOUR.astimezone(ET_TZ).year
DEFAULT_ARCHIVE_DIR_BASE = f"/data/logs_archive/site/fastly"

TIME_PATTERN = r"\[([^\]]+)\]"
"""Pattern to capture time from a log line.

Ex.
180.66.144.48 180.66.144.48 - | [29/Dec/2023:01:57:01 +0000] [Mozilla/etc...
"""

TIME_STRP = "%d/%b/%Y:%H:%M:%S %z"

def _filename_only(name: str) -> str:
    return name.split("/")[-1]


def _keyed(line: str):
    match = re.search(TIME_PATTERN, line)
    if match:
        return datetime.strptime(match.group(1), TIME_STRP), line
    else:
        return None

def _invert_keyed(data) -> str:
    return data[1]

def k_way_merge(
        in_files: List[Path],
        out_file: Path) -> None:
    """Merges k different log files in time order.

    Outline:
    Open all N files,
    until done:
      read 1 line from each and put on heap, save one line from heap

    This will time order the files if they files are in order to begin with.  If
    they are not in order it should preserve some semblance of order in as much
    as the original files were ordered. Perfect order is not necessary for the
    web logs since they are not usually in order to begin with.

    Parameters
    ----------
    files: Paths to read from
    output: Path to write output to
    """
    files = [open(filename) for filename in in_files]
    line_heap = []
    heapq.heapify(line_heap)
    with open(out_file, 'w') as out_fh:
        try:
            while files:
                for i, file in enumerate(files):  # get a line from each file
                    line = file.readline()
                    if not line:  # handle file is out of lines
                        file.close()
                        files.pop(i)
                        continue
                    else:
                        with_key = _keyed(line.strip())
                        if with_key is None:
                            print("Warning, no date found in log line, skipping.")
                        else:
                            heapq.heappush(line_heap, with_key)

                # now that we have at least one line from each file, get the earliest
                earliest_line = _invert_keyed(heapq.heappop(line_heap))
                out_fh.write( earliest_line + '\n')

            while line_heap:  # files empty but still lines in line_heap
                earliest_line = _invert_keyed(heapq.heappop(line_heap))
                out_fh.write(earliest_line + '\n')
        finally:
            [f.close() for f in files]


def download_files(bucket: str = DEFAULT_BUCKET,
                   date: datetime = UTC_PREVIOUS_HOUR,
                   key_pattern: Optional[str] = None,
                   max: int = 0,
                   out_dir: Path = Path(TMP_DIR)) -> List[Path]:
    """Gets fastly log files for the last hour, combines them into a single file and saves that.

    Parameters
    ----------
    verbose: if verbose or not
    bucket: the GS bucket. Should be a string without the "gs://"
    key_pattern: The key pattern for the files. Should not have a leading /.
    out_dir: Output directory to save log files in.

    Returns
    -------
    Path
    """
    if key_pattern is None:
        key_pattern = f"site/fastly/{date.year}/fastly_access_log.{date.strftime('%Y-%m-%d')}T{date.hour:02d}"

    logger.debug(f"Getting logs for gs://{bucket}/{key_pattern}")
    logger.debug(f"Writing to {out_dir}")
    out_dir.mkdir(exist_ok=True)
    credentials, project_id = google.auth.default()
    if hasattr(credentials, "service_account_email"):
        logger.debug(f"Using service account: {credentials.service_account_email}")
    else:
        logger.warning("WARNING: no service account credentials.")

    client = storage.Client()
    blobs = client.list_blobs(DEFAULT_BUCKET, prefix=key_pattern)
    files: List[Path] = []
    for i, blob in enumerate(blobs):
        if max and i > max:
            break
        dl_name = out_dir / _filename_only(blob.name)
        unzip_name = out_dir / str(dl_name.name).removesuffix('.gz')
        blob.download_to_filename(dl_name)
        logger.debug(f"Downloaded {dl_name}")
        if dl_name.suffix == ".gz":
            os.system(f"gunzip --stdout \"{dl_name}\" > \"{unzip_name}\"")
            dl_name.unlink()
            files.append(unzip_name)
        else:
            files.append(dl_name)
    logger.debug(f"downloaded {len(files)} saved to {out_dir}")
    return files

def sort_files_by_time(files: list[Path]) -> list[Path]:
    """The logs from fastly are not sorted."""
    out_files = []
    for i, file in enumerate(files):
        tmpf = file.with_name(file.name + ".sorted")
        with open(file, 'r') as infile, open(tmpf, 'w') as outfile:
            sorted_lines = []
            lines = infile.readlines()
            for line in lines:
                match = re.search(TIME_PATTERN, line,)
                if not match:
                    logger.warning("no time found in log line during sorting")
                    continue
                sorted_lines.append( (match.group(1), line))
            sorted_lines.sort()
            outfile.writelines([item[1] for item in sorted_lines])
        out_files.append(tmpf)
        file.unlink()
    return out_files


def get_hour(date_of_logs: datetime|str = "previous_hour",
             out_file: Path = None,
             tmp_dir: Path = Path(TMP_DIR),
             with_db_stats: bool = False):
    """Gets the fastly logs for an hour.

    Downloads the fastly logs from GCP, combines them and puts in
    logs_archive.

    By default, gets the previous hour.

    File names and timestamps in logs will be UTC time since fastly uses
    UTC times.

    Will overwrite already existing out file and will overwrite any
    already downloaded log files.
    """
    if date_of_logs == "previous_hour":
        date_of_logs = UTC_PREVIOUS_HOUR
    elif type(date_of_logs) == str:
        date_of_logs = dateutil.parser.parse(date_of_logs)

    if not( date_of_logs.tzinfo is not None and date_of_logs.tzinfo.utcoffset(date_of_logs) != 0):
        raise ValueError(f"date_of_logs must have a timezone and it must be UTC, it was {date_of_logs}")

    # Since arXiv logs are stored with ET, we also need ET
    et_time = date_of_logs.astimezone(pytz.timezone("US/Eastern"))

    out_dir = Path(tmp_dir)
    out_dir.mkdir(exist_ok=True)

    if out_file is None:
        archive_dir = Path(DEFAULT_ARCHIVE_DIR_BASE) / str(et_time.year)
        archive_dir.mkdir(exist_ok=True)
        # outfile is with ET since that is similar to the other arxiv logs
        out_file = archive_dir / f"fastly_access_logs.{et_time.astimezone().isoformat()}.log"

    logger.debug(f"Getting fastly logs for {et_time}ET (UTC {date_of_logs})")
    files = download_files(date=date_of_logs)
    logger.debug(f"Merging {len(files)} files.")
    k_way_merge(files, out_file=out_file)
    logger.debug(f"Wrote to {out_file}")
    [file.unlink() for file in files]
    logger.debug(f"Cleaned up {len(files)}")
    if with_db_stats:
        expect_utc = "-u"
        local_date = f"-d {et_time.isoformat()}"
        web_node = "-n 0"
        cmd = f"""~/bin/cron/load_hourly_stats.pl -l {expect_utc} {web_node} {local_date} -f {out_file}"""
        logger.debug("Doing load_hourly_stats: " + cmd)
        os.system(cmd)

    logger.debug(f"Done getting hour {et_time}")


def fn_combine_day(date_eastern: datetime|str=None):
    """Combine the files for a day into a single file.

    Defaults to yesterday US/Eastern if no date_eastern.
    """
    if date_eastern is None:
        date_eastern = datetime.now().astimezone(ET_TZ).replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=1)
    elif type(date_eastern) == str:
        date_eastern = dateutil.parser.parse(date_eastern)

    la_dir = Path(DEFAULT_ARCHIVE_DIR_BASE) / str(date_eastern.year)
    logger.debug(f"Going to combine for {date_eastern} in dir {la_dir}")

    files = la_dir.glob(f"fastly_access_logs.{date_eastern.strftime('%Y-%m-%d')}T*.log")
    if not files:
        raise RuntimeError(f"No log files found in {la_dir} for date_eastern.strftime('%Y-%m-%d')")

    outfile = la_dir / f"fastly_access_log.{date_eastern.strftime('%Y-%m-%d')}.log"
    if outfile.exists():
        raise RuntimeError(f"Was going to write log to {outfile} but it already exists. Aborting")

    outfile_gz = la_dir / f"fastly_access_log.{date_eastern.strftime('%Y-%m-%d')}.log.gz"
    if outfile_gz.exists():
        raise RuntimeError(f"Was going to write log to {outfile_gz} but it already exists. Aborting")

    with open(outfile , "wb") as outfh:
        for infile in files:
            logger.debug(f"Concat {infile}")
            with open(infile, "rb") as infh:
                shutil.copyfileobj(infh, outfh)
            infile.unlink()

    os.system(f"gzip --force {outfile}")
    logger.debug(f"Gzipped to {outfile}.gz")



def get_day(date_eastern: datetime|str,
            tmp_dir: Path = Path(TMP_DIR),
            with_db_stats: bool = False,
            combine_day: bool = False):
    """Gets all logs for a day.

    `date_eastern` is in the ET.
    """
    logger.setLevel(logging.DEBUG)

    if type(date_eastern) == str:
        date_eastern = dateutil.parser.parse(date_eastern)
    elif not( date_eastern.tzinfo is not None):
        raise ValueError(f"date_eastern must have a timezone and it should be ET, it was {date_eastern}")

    for hour in range(0,24):
        utc_h = date_eastern.replace(hour=hour).astimezone(pytz.timezone("UTC"))
        get_hour(date_of_logs=utc_h, tmp_dir=tmp_dir, with_db_stats=with_db_stats)

    if combine_day:
        fn_combine_day(date_eastern)



def date_range(start: date|str, end: date|str,
               tmp_dir: Path = Path(TMP_DIR),
               with_db_stats: bool = False,
               combine_day: bool = False):
    """Do `get_day` for all days in a date range, inclusive."""
    if type(start) == str:
        start = dateutil.parser.parse(start).replace(hour=12, minute=0, second=0, microsecond=0)
        #start = ET_TZ.localize(start)
        start = start.astimezone(ET_TZ)
    if type(end) == str:
        end = dateutil.parser.parse(end).replace(hour=12, minute=0, second=0, microsecond=0)
        #end = ET_TZ.localize(end)
        end = end.astimezone(ET_TZ)

    if start > end:
        raise ValueError(f"start ({start}) must be earlier than end ({end})")


    oneday = timedelta(days=1)
    workingday = start
    while(workingday <= end):
        get_day(workingday, tmp_dir, with_db_stats, combine_day)
        workingday = workingday + oneday



if __name__ == "__main__":
    fire.Fire({
        'get_day': get_day,
        'get_hour': get_hour,
        'combine_day': fn_combine_day,
        'date_range': date_range,
        }
    )
