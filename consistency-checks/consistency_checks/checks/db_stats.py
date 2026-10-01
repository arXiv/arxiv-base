"""Weekly DB stats, moderation gaps and search engine index counts.

Port of arxiv-bin cron/db_stats.pl.
"""

import argparse
import json
import os
import time
import urllib.parse
import urllib.request

from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES
from sqlalchemy import Connection, text

from ..core import DB_STATS_ADDRESSES, Context, Report

FMT = "{:>40}  {:>7}  {:>7}  {}"
MOD_CHECK_DAYS = 30
EXCLUDED_FROM_MOD_CHECK = ("physics.gen-ph", "math.GM", "math.HO", "cs.OH")

DEFAULT_INDEX_HOSTS = (
    "arxiv.org,export.arxiv.org,arxiv4.library.cornell.edu,"
    "lib-arxiv-003.serverfarm.cornell.edu,arxiv1.library.cornell.edu,"
    "www.arxiv.org,dev.arxiv.org,beta.arxiv.org,cul.arxiv.org"
)
DEFAULT_GOOGLE_CX = "004880366723946616036:ilkvvcitlam"


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--days", type=int, default=7, help="'new' window in days (default 7)")
    p.add_argument("--no-search-counts", action="store_true", help="skip Google/Bing index counts")


def _count(conn: Connection, sql: str, **params) -> int:
    return conn.execute(text(sql), params).scalar_one()


def _tot_new(heading: str, tot: int, new: int | None) -> str:
    return FMT.format(heading, f"{tot:7d}", "" if new is None else f"({new:5d})", "")


def _tot_new_pct(heading: str, tot: int, ttot: int, new: int, tnew: int) -> str:
    tot_pct = f"{100 * tot / ttot:6.1f}%" if ttot else "---"
    new_pct = f"({100 * new / tnew:4.1f}%)" if tnew else "---"
    return FMT.format(heading, tot_pct, new_pct, f"( {tot} / {ttot}, {new} / {tnew} )")


def db_stats(conn: Connection, ctx: Context, days: int) -> list[str]:
    since_epoch = int(time.time()) - 86400 * days
    since_dt = ctx.db_days_ago(days)
    c = lambda sql: _count(conn, sql, e=since_epoch, d=since_dt)
    label = "week" if days == 7 else f"{days} days"
    out = [f"## User and article stats with (changes in last {label})", ""]

    out.append(
        _tot_new(
            "Registered users",
            c("SELECT COUNT(*) FROM tapir_users"),
            c("SELECT COUNT(*) FROM tapir_users WHERE joined_date > :e"),
        )
    )
    owners = "SELECT COUNT(DISTINCT u.user_id) FROM tapir_users u JOIN arXiv_paper_owners o ON u.user_id = o.user_id"
    out.append(_tot_new("Registered users with articles", c(owners), c(owners + " WHERE u.joined_date > :e")))
    out.append(
        _tot_new("Moderators", c("SELECT COUNT(DISTINCT user_id) FROM arXiv_moderators WHERE archive != 'test'"), None)
    )
    out.append(
        _tot_new(
            "Author ids",
            c("SELECT COUNT(*) FROM arXiv_author_ids"),
            c("SELECT COUNT(*) FROM arXiv_author_ids WHERE updated > :d"),
        )
    )
    out.append("")

    out.append(
        _tot_new(
            "Articles",
            c("SELECT COUNT(*) FROM arXiv_documents"),
            c("SELECT COUNT(*) FROM arXiv_documents WHERE dated > :e"),
        )
    )
    anc = "FROM arXiv_metadata WHERE source_flags LIKE '%A%' AND is_current = 1"
    latest = conn.execute(text(f"SELECT paper_id {anc} ORDER BY created DESC LIMIT 1")).scalar()
    out.append(
        _tot_new(
            f"Articles w anc files (latest: {latest})",
            c(f"SELECT COUNT(*) {anc}"),
            c(f"SELECT COUNT(*) {anc} AND created > :d"),
        )
    )

    for prefix, cond in (("Versions", "1=1"), ("Current versions", "is_current = 1")):
        base = f"SELECT COUNT(*) FROM arXiv_metadata WHERE {cond}"
        n, n_recent = c(base), c(base + " AND created > :d")
        for heading, extra in (
            ("missing affiliation", "authors NOT LIKE '%(%'"),
            ("with et al", "authors LIKE '%et al%'"),
        ):
            out.append(
                _tot_new_pct(
                    f"{prefix} {heading}",
                    c(f"{base} AND {extra}"),
                    n,
                    c(f"{base} AND created > :d AND {extra}"),
                    n_recent,
                )
            )
    return out


def _cats_with_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{cat} ({n})" for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]))


def moderator_stats(conn: Connection) -> list[str]:
    mods = {f"{a}.{sc or ''}" for a, sc in conn.execute(text("SELECT archive, subject_class FROM arXiv_moderators"))}
    since = int(time.time()) - 86400 * MOD_CHECK_DAYS
    q = text(
        "SELECT COUNT(*) FROM arXiv_documents d JOIN arXiv_in_category c ON d.document_id = c.document_id "
        "WHERE c.archive = :a AND c.subject_class = :sc AND d.dated > :since"
    )
    excluded = {cat: 0 for cat in EXCLUDED_FROM_MOD_CHECK}
    with_overall: dict[str, int] = {}
    no_overall: dict[str, int] = {}
    for archive in sorted(a.id for a in ARCHIVES.values() if a.is_active and a.id != "test"):
        cats = sorted(c.id for c in CATEGORIES.values() if c.in_archive == archive and c.is_active)
        for cat in cats or [archive]:
            a, _, sc = cat.partition(".")
            if f"{a}.{sc}" in mods:
                continue
            n = conn.execute(q, {"a": a, "sc": sc, "since": since}).scalar_one()
            if cat in excluded:
                excluded[cat] = n
            elif f"{archive}." in mods:
                with_overall[cat] = n
            else:
                no_overall[cat] = n
    out = [f"## Moderation gaps with (submissions in last {MOD_CHECK_DAYS} days)"]
    if no_overall:
        out.append(
            "\nCategories missing moderators in archives without overall moderator: " + _cats_with_counts(no_overall)
        )
    if with_overall:
        out.append("\nCategories missing moderators with archive moderator(s): " + _cats_with_counts(with_overall))
    out.append("\nCategories excluded from moderator check: " + _cats_with_counts(excluded))
    return out


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "arXiv index monitor"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def google_counts() -> list[str]:
    out = [
        "## Google index counts for different server names",
        "",
        (
            "These are approximate and it seems that the custom API does not agree with normal 'site:' "
            "search. Any large number for a site other than arxiv.org is a cause for concern."
        ),
        "",
    ]
    key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    if not key:
        return out + ["(skipped: GOOGLE_SEARCH_API_KEY not set)"]
    cx = os.environ.get("GOOGLE_SEARCH_CX", DEFAULT_GOOGLE_CX)
    for host in os.environ.get("SEARCH_INDEX_HOSTS", DEFAULT_INDEX_HOSTS).split(","):
        url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(
            {"key": key, "cx": cx, "q": f"site:{host}"}
        )
        try:
            total = _get_json(url)["queries"]["request"][0]["totalResults"]
            out.append(f"{host:>40} {int(total)}")
        except Exception as e:  # noqa: BLE001 - one failing host/API must not break the report
            out.append(f"{host:>40} (failed to query google: {e})")
    return out


def bing_counts() -> list[str]:
    out = ["## Bing index counts. Not sure how this data separates or includes sub-domains", ""]
    key = os.environ.get("BING_API_KEY")
    if not key:
        return out + ["(skipped: BING_API_KEY not set)"]
    url = "https://ssl.bing.com/webmaster/api.svc/json/GetCrawlStats?" + urllib.parse.urlencode(
        {"siteUrl": "http://arxiv.org/", "apikey": key}
    )
    try:
        latest = _get_json(url)["d"][-1]  # day order, latest last
        out.append(f"{'arxiv.org':>40} {int(latest['InIndex'])}")
    except Exception as e:  # noqa: BLE001 - a failing API must not break the report
        out.append(f"{'arxiv.org':>40} Failed to get results from bing API (got: {e})")
    return out


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("arXiv DB stats", DB_STATS_ADDRESSES, always_send=True)
    with ctx.engine.connect() as conn:
        report.lines += db_stats(conn, ctx, args.days) + [""] + moderator_stats(conn)
    if not args.no_search_counts:
        report.lines += [""] + google_counts() + [""] + bing_counts()
    report.info(f"\n[Report from consistency-checks db_stats at {time.ctime()}]")
    return report
