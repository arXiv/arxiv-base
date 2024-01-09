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
from pathlib import Path
from typing import Optional, List

import google.auth
from google.cloud import storage

import fire

logging.basicConfig()
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

TMP_DIR="/tmp"  # needs reasonable temp FS, 600MB of work space

DEFAULT_BUCKET="arxiv-logs-archive"
DEFAULT_KEY="site/fastly/" + datetime.utcnow().strftime("%Y/fastly_access_log.%Y-%m-%dT%H")

_previous_hour = datetime.utcnow().replace(minute=00) - timedelta(hours=1)
UTC_NOW = _previous_hour.strftime("%Y-%m-%dT%H")
UTC_DATE = _previous_hour.date()
UTC_HOUR = _previous_hour.hour

DEFAULT_OUT_DIR=f"/data/logs_archive/site/fastly/{_previous_hour.year}/"

TIME_PATTERN=r"\[([^\]]+)\]"
"""Pattern to caputre time from a log line
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
    #files = [gzip.open(filename) for filename in in_files]
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


def download_files(verbose: bool = False,
             bucket: str = DEFAULT_BUCKET,
             date: date = UTC_DATE,
             hour: int = UTC_HOUR,
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
        key_pattern = f"site/fastly/{date.year}/fastly_access_log.{date.strftime('%Y-%m-%d')}T{hour}"

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
            logger.debug(f"Will ungzip to {unzip_name}")
            os.system(f"gunzip --stdout \"{dl_name}\" | sort -o \"{unzip_name}\"")
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


def get_fastly_logs(date_of_logs: date = _previous_hour.date(),
                    hour: int = _previous_hour.hour,
                    out_file: Path = None,
                    tmp_dir: Path = Path(TMP_DIR)):
    """Gets the fastly logs for an hour.

    Downloads the fastly logs from GCP, combines them and puts in logs_archive.

    By default, gets the previous hour.

    File names and timestamps in logs will be UTC time since fastly uses UTC times.

    Will overwrite already existing out file and will overwrite any already downloaded log files.
    """
    if out_file is None:
        out_dir = Path(tmp_dir)
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / f"fastly_access_logs.{date_of_logs.strftime('%Y-%m-%d')}T{hour}.log"

    files = download_files(date=date_of_logs, hour=hour)
    k_way_merge(files, out_file=out_file)
    [file.unlink() for file in files]

def _test():
    logger.setLevel(logging.DEBUG)
    d = date(2023,12,30)
    h = 2
    files = download_files(verbose=True, hour=h, date=d, max=4)
    #files = sort_files_by_time(files)
    k_way_merge(files,
                files[0].with_name(f"fastly_access_MERGED.{d.strftime('%Y-%m-%d')}T{h}.log"))


if __name__ == "__main__":
    fire.Fire(get_fastly_logs)
