"""Categories of every current version: valid, canonical, and in agreement
between the abs file, arXiv_in_category (the master) and
arXiv_metadata.abs_categories.

Merges arxiv-bin crosses.pl -C (read-only; its DB fix modes were dropped) and
test/check_categories.pl -a.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from google.api_core.exceptions import NotFound

from ..categories import Categories, abs_field
from ..core import CRON_ERRORS_ADDRESS, Context, Report
from ..papers import in_category, month_versions, paper_key, parse_yymms, split_id
from ..store import Store


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--yymm", help="limit to months, e.g. 2101,2103-2105 (default: all)")


def db_categories(rows: list[tuple[str, str, bool]], pid: str, problems: list[str]) -> Categories:
    cats = Categories()
    for archive, sc, is_primary in rows:
        cat = f"{archive}.{sc}" if sc else archive
        if is_primary and cats.primary:
            problems.append(f"{pid}: MORE THAN ONE primary in db: {cats.primary} and {cat}")
            cats.add_secondary(cat)
        elif is_primary:
            cats.primary = cat
        else:
            cats.add_secondary(cat)
    cats.primary = cats.primary or "NO_PRIMARY"
    return cats


def read_abs_categories(store: Store, pid: str) -> str | None:
    try:
        with store.open(paper_key("ftp", pid, "abs")) as f:
            return abs_field(f.read().decode("latin-1"), "Categories")
    except (FileNotFoundError, NotFound):
        return None


def check_paper(pid: str, abs_cats: str | None, db_rows, dbcp: str) -> list[str]:
    if abs_cats is None:
        return [f"{pid}: Can't read categories from abs {paper_key('ftp', pid, 'abs')}"]
    problems: list[str] = []
    cats = Categories(abs_cats)
    cats_str = str(cats)

    # check_categories.pl
    if not cats.is_valid_for_id(pid):
        problems.append(f"{pid}: Invalid categories: {cats_str}")
    else:
        canon = Categories(cats_str)
        if canon.canonicalize() > 0:
            problems.append(f"{pid}: Non-canonical categories: {cats_str} should be {canon}")

    # crosses.pl
    dbcats_str = str(db_categories(db_rows, pid, problems))
    if dbcats_str == cats_str:
        if dbcats_str != dbcp:
            problems.append(f"{pid}: WARNING, db and abs match but dbcp bad: db: {dbcats_str} dbcp: {dbcp}")
    else:
        with_aliases = Categories(dbcats_str)
        with_aliases.canonicalize()
        aliases_only = " IN ALIASES ONLY" if str(with_aliases) == cats_str else ""
        problems.append(f"{pid}: MISMATCH{aliases_only}: abs: {cats_str} db: {dbcats_str}")
    return problems


def check_month(ctx: Context, pool: ThreadPoolExecutor, yymm: str) -> tuple[int, list[str]]:
    with ctx.engine.connect() as conn:
        current = [v for v in month_versions(conn, yymm) if v.is_current and split_id(v.paper_id)[0] != "test"]
        db_rows: dict[int, list] = defaultdict(list)
        for doc_id, archive, sc, is_primary in in_category(conn, [v.document_id for v in current]):
            db_rows[doc_id].append((archive, sc, is_primary))

    # several current rows for one paper would be a DB error in itself
    dbcp: dict[str, list[str]] = defaultdict(list)
    for v in current:
        dbcp[v.paper_id].append(v.abs_categories or "")
    by_pid = {v.paper_id: v for v in current}

    pids = sorted(by_pid)
    abs_cats = pool.map(lambda p: read_abs_categories(ctx.store, p), pids)
    problems = []
    for pid, cats in zip(pids, abs_cats):
        problems += check_paper(pid, cats, db_rows[by_pid[pid].document_id], " #EXTRA# ".join(dbcp[pid]))
    return len(pids), problems


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("Categories check", CRON_ERRORS_ADDRESS)
    n = 0
    # ponytail: months run one after the other, abs reads within a month in parallel
    with ThreadPoolExecutor(ctx.settings.workers) as pool:
        for yymm in parse_yymms(args.yymm):
            count, problems = check_month(ctx, pool, yymm)
            n += count
            for p in problems:
                report.problem(p)
    report.info(f"Looked at {n} items, {report.problems} warnings.")
    return report
