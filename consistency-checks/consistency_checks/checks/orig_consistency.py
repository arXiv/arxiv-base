"""ftp/ and orig/ hold exactly the files the DB says they should.

Port of arxiv-bin cron/check_files_in_orig.pl and the existence part of
test/check_abs_src_files.pl (ownership/mode checks are meaningless in a
bucket and were dropped).

For every paper in arXiv_metadata, month by month:
  ftp/<archive>/papers/<yymm>/<id>.{abs,<src>}        current version
  orig/<archive>/papers/<yymm>/<id>v<N>.{abs,<src>}   each older version
Each must be exactly two files: abs + source. A withdrawn version only
needs the abs. Anything else in those month directories, and stray entries
anywhere above them in orig/, is reported.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from arxiv.legacy.papers.deleted import get_deleted_data

from ..core import SHERIFF_ADDRESS, Context, Report
from ..papers import month_versions, paper_dir, parse_key, parse_yymms, split_id
from ..store import Store

AREAS = ("ftp", "orig")
# Left over from the CIT file system sync; the Perl check ignored them too.
IGNORED_FILES = {"arxiv-sync.txt", ".cit_nfs_mount_test"}
SKIPPED_ARCHIVES = {"test"}
MAX_PARALLEL_MONTHS = 8  # each holds a DB connection; SQLAlchemy's default pool is 5 + 10


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--yymm", help="limit to months, e.g. 2101,2103-2105 (default: all)")


def scan_layout(store: Store, area: str) -> tuple[set[str], list[str]]:
    """Month directories under <area>/<archive>/papers/, and stray entries.

    Strays are only reported for orig/: ftp/<archive>/ also holds listings/
    and READMEs, which the Perl check never looked at either.
    """
    month_dirs: set[str] = set()
    stray: list[str] = []

    def strays(prefix: str, files) -> list[str]:
        return [o.key for o in files if o.key != prefix and o.key.rsplit("/", 1)[-1] not in IGNORED_FILES]

    archives, files = store.list_dir(f"{area}/")
    stray += strays(f"{area}/", files)
    for archive_dir in archives:
        if archive_dir.split("/")[1] in SKIPPED_ARCHIVES:
            continue
        subdirs, files = store.list_dir(archive_dir)
        stray += strays(archive_dir, files)
        for sub in subdirs:
            if sub == f"{archive_dir}papers/":
                months, files = store.list_dir(sub)
                month_dirs.update(months)
                stray += strays(sub, files)
            else:
                stray.append(sub)
    return month_dirs, (stray if area == "orig" else [])


def check_month(ctx: Context, yymm: str, month_dirs: set[str], deleted: set[str]) -> list[str]:
    with ctx.engine.connect() as conn:
        versions = month_versions(conn, yymm)
    expected: dict[str, dict[int, bool]] = defaultdict(dict)  # paper_id -> {version: withdrawn}
    for v in versions:
        if split_id(v.paper_id)[0] not in SKIPPED_ARCHIVES:
            expected[v.paper_id][v.version] = v.is_withdrawn

    dirs = {d for d in month_dirs if d.rstrip("/").endswith(f"/{yymm}")}
    dirs |= {paper_dir(area, pid) for pid in expected for area in AREAS}

    problems = []
    found: dict[tuple[str, str, int | None], list[str]] = defaultdict(list)  # (area, id, v) -> exts
    for d in sorted(dirs):
        area = d.split("/", 1)[0]
        for obj in ctx.store.objects(d):
            if obj.key.endswith("/"):  # directory placeholder object
                continue
            parsed = parse_key(obj.key)
            if parsed is None or paper_dir(area, parsed.paper_id) != d:
                problems.append(f"BAD FILE: {obj.key}")
            else:
                found[(area, parsed.paper_id, parsed.version)].append(parsed.ext)

    def check(label: str, exts: list[str], withdrawn: bool) -> None:
        ok = "abs" in exts and (len(exts) == 2 or (withdrawn and len(exts) == 1))
        if not ok:
            problems.append(f"{label}: bad number of files: {len(exts) or 'NONE!'} ({', '.join(sorted(exts))})")

    for pid, vers in sorted(expected.items()):
        current = max(vers)
        check(f"{pid} (ftp, v{current})", found.pop(("ftp", pid, None), []), vers[current])
        for v in range(1, current):
            check(f"{pid}v{v} (orig)", found.pop(("orig", pid, v), []), vers.get(v, False))

    for (area, pid, v), exts in sorted(found.items(), key=str):
        if area == "ftp" and v is None and pid in deleted:
            continue  # deleted papers keep files but have no DB rows; see deleted_papers
        what = "no DB record" if pid not in expected else "not an expected version"
        name = split_id(pid)[2] + (f"v{v}" if v else "")
        problems.append(f"{pid}: unexpected files in {area} ({what}): {name}.{{{','.join(sorted(exts))}}}")
    return problems


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("ERROR IN FTP/ORIG FILES CHECK", SHERIFF_ADDRESS)
    deleted = set(get_deleted_data())
    month_dirs: set[str] = set()
    for area in AREAS:
        dirs, stray = scan_layout(ctx.store, area)
        month_dirs |= dirs
        for key in stray:
            report.problem(f"BAD FILE: {key}")

    yymms = parse_yymms(args.yymm)
    # ponytail: months run in parallel, each month's listing is sequential;
    # split a month further if a single month ever dominates the runtime.
    with ThreadPoolExecutor(min(ctx.settings.workers, MAX_PARALLEL_MONTHS)) as pool:
        for problems in pool.map(lambda m: check_month(ctx, m, month_dirs, deleted), yymms):
            for p in problems:
                report.problem(p)
    report.info(f"Checked {len(yymms)} months, {report.problems} errors.")
    return report
