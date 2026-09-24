"""Integrity of recently written paper files in ftp/ and orig/.

Port of arxiv-bin cron/check_recently_updated_articles.pl. Instead of
`find -ctime` over the file system, the papers come from arXiv_metadata rows
created/updated in the window, and their objects are kept if the bucket
object was written in the window.

Checks: .tar.gz lists, .gz decompresses, pdfinfo reports no (unignored)
errors, .abs parses with canonical Categories and a valid License.
"""

import argparse
import gzip
import re
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

from arxiv.document.parse_abs import parse_abs
from arxiv.license import LICENSES
from sqlalchemy import text

from ..categories import Categories, abs_field
from ..core import SHERIFF_ADDRESS, Context, Report
from ..papers import paper_dir, parse_key, split_id, yyyymm
from ..store import Obj, Store

# pdfinfo stderr we don't act on (ARXIVCE-3422)
PDFINFO_IGNORED = (
    r"Bad annotation destination",
    r"Error: PDF version 1\.[67]",
    r"Error: Expected the default config, but ",
    r"Error: Expected the optional content group list",
    r"xref num",
    r"Suspects object is wrong type",
    r"Invalid least number of objects reading page offset hints table",
    r"Syntax Error: Invalid XRef entry",
    r"Syntax Error: Can.t get Fields array",
    r"Syntax Warning: Invalid number of shared object groups",
)
PDFINFO_IGNORE = re.compile("|".join(PDFINFO_IGNORED))
CHUNK = 1 << 20


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--days", type=float, default=1, help="look at files up to DAYS old (default 1)")


def _short(msg: str) -> str:
    msg = msg.strip()
    if len(msg) > 200:
        msg = f"{msg[:200]} [truncated from {len(msg)} chars]"
    return msg.replace("\n", " ")


def check_tar(store: Store, key: str) -> str | None:
    with store.open(key) as f, tarfile.open(fileobj=f, mode="r|gz") as tar:
        for _ in tar:  # walking the stream validates headers and the gzip CRC
            pass
    return None


def check_gz(store: Store, key: str) -> str | None:
    with store.open(key) as f, gzip.GzipFile(fileobj=f) as gz:
        while gz.read(CHUNK):
            pass
    return None


def check_pdf(store: Store, key: str) -> str | None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "file.pdf"
        store.download(key, path)
        res = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, errors="replace", check=False)
    errors = [line for line in res.stderr.splitlines() if line.strip() and not PDFINFO_IGNORE.search(line)]
    return "\n".join(errors) or None


def check_abs(store: Store, key: str) -> list[str]:
    with store.open(key) as f:
        raw = f.read().decode("latin-1")
    try:
        parse_abs(raw, datetime.now(UTC))
    except Exception as e:  # noqa: BLE001 - any parse failure is a BAD ABS finding
        return [f"BAD ABS: {key} ({_short(str(e) or type(e).__name__)})\n"]

    problems = []
    cat_str = abs_field(raw, "Categories") or ""
    cats = Categories(cat_str)
    cats.canonicalize()
    if cat_str != str(cats):
        problems.append(f"NON CANONICAL Categories: {key}\n current   = {cat_str}\n canonical = {cats}\n")
    parsed = parse_key(key)
    lic = abs_field(raw, "License")
    if lic:
        if lic not in LICENSES:
            problems.append(f"Invalid license in {key}: '{lic}'")
    elif parsed and yyyymm(split_id(parsed.paper_id)[1]) >= 200803:
        problems.append(f"Missing License in {key}")
    return problems


def check_object(store: Store, obj: Obj) -> list[str]:
    key = obj.key
    try:
        if key.endswith(".abs"):
            return check_abs(store, key)
        if key.endswith(".tar.gz"):
            err = check_tar(store, key)
        elif key.endswith(".gz"):
            err = check_gz(store, key)
        elif key.endswith(".pdf"):
            err = check_pdf(store, key)
        else:
            return [f"unknown file type: {key}"]
    except Exception as e:  # noqa: BLE001 - any read/decompress failure is a BAD FILE finding
        err = str(e) or type(e).__name__
    return [f"BAD FILE: {key} {_short(err)}\n"] if err else []


def recent_objects(store: Store, paper_id: str, since: datetime) -> list[Obj]:
    stem = split_id(paper_id)[2]
    found = [
        *store.objects(f"{paper_dir('ftp', paper_id)}{stem}."),
        *store.objects(f"{paper_dir('orig', paper_id)}{stem}v"),
    ]
    return [o for o in found if o.updated >= since and not o.key.endswith("/")]


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("ERROR IN FILESYSTEM CHECKS", SHERIFF_ADDRESS)
    since = datetime.now(UTC) - timedelta(days=args.days)
    # pad the DB window a day: DB times are local, and bucket times decide anyway
    db_since = ctx.db_days_ago(args.days + 1)
    with ctx.engine.connect() as conn:
        paper_ids = sorted(
            {
                r[0]
                for r in conn.execute(
                    text("SELECT paper_id FROM arXiv_metadata WHERE created >= :d OR updated >= :d"), {"d": db_since}
                )
            }
        )
    paper_ids = [p for p in paper_ids if split_id(p)[0] != "test"]

    store = ctx.store
    with ThreadPoolExecutor(ctx.settings.workers) as pool:
        objs = [o for found in pool.map(lambda p: recent_objects(store, p, since), paper_ids) for o in found]
        results = list(pool.map(lambda o: check_object(store, o), objs))

    report.info(f"Found {len(objs)} files which have changed in the last {args.days:g} days.")
    for problems in results:
        for p in problems:
            report.problem(p)
    report.info(f"Checks complete, {report.problems} errors.")
    return report
