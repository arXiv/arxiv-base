"""Warn about new accounts matching the FLAGS patterns.

Port of arxiv-bin cron/watch_new_accounts.pl + arXiv::Admin::CheckAccounts/Flags.

FLAGS file format: blank lines ignored; '# comment' lines set the comment
for the patterns that follow; every other line is a pattern, several
regexes joined by ' && ' must all match. A missing file means no patterns
(the job runs without the flags secret mounted).
"""

import argparse
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from ..core import DB_TZ, SYSTEM_QUEUE_ADDRESS, Context, Report

DEFAULT_FLAGS_FILE = "/secrets/flags/FLAGS"

logger = logging.getLogger(__name__)


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--hours", type=float, default=24, help="look back this many hours (default 24)")
    p.add_argument(
        "--flags-file",
        default=DEFAULT_FLAGS_FILE,
        help=f"FLAGS patterns file, mounted from Secret Manager (default {DEFAULT_FLAGS_FILE})",
    )


def read_flags(path: str | Path) -> dict[str, str]:
    flags: dict[str, str] = {}
    if not Path(path).is_file():
        logger.warning("No FLAGS file at %s, checking no patterns", path)
        return flags
    comment = ""
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comment = line.lstrip("#").strip()
        else:
            flags[line] = comment
    return flags


def check_string(flags: dict[str, str], s: str) -> list[str]:
    warnings = []
    for pattern, comment in flags.items():
        matches = []
        for part in re.split(r"\s+&&\s+", pattern):
            m = re.search(part, s)
            if not m:
                break
            matches.append(m.group(0))
        else:
            warnings.append(f"FLAGS: found '{' && '.join(matches)}', perhaps {comment}")
    return warnings


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("arXiv NEW ACCOUNT WARNINGS", SYSTEM_QUEUE_ADDRESS)
    flags = read_flags(args.flags_file)
    since = int(time.time() - args.hours * 3600)
    with ctx.engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT u.user_id, n.nickname, u.joined_date, u.first_name, u.last_name, d.affiliation, u.email "
                "FROM tapir_users u JOIN arXiv_demographics d ON u.user_id = d.user_id "
                "JOIN tapir_nicknames n ON u.user_id = n.user_id "
                "WHERE u.joined_date >= :since ORDER BY u.joined_date"
            ),
            {"since": since},
        ).all()

    report.info(f"Looked for patterns in new accounts created in past {args.hours:.1f} hours, found:\n")
    for user_id, nickname, joined, *rest in rows:
        s = ", ".join(str(x or "") for x in (nickname, *rest))
        if warnings := check_string(flags, s):
            joined_str = datetime.fromtimestamp(joined, DB_TZ).strftime("%Y-%m-%d %H:%M:%S")
            report.problem(
                f"new account {nickname} ({user_id}, joined {joined_str})\n  {s}\n  WARNINGS: "
                + "\n".join(warnings)
                + "\n"
            )
    if not report.problems:
        report.info("nothing")
    return report
