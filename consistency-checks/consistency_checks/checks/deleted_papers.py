"""Deleted papers: zero-size abs, source kept, no DB rows.

Port of arxiv-bin test/check_deleted_papers.pl. The deleted list comes from
deleted.json (arxiv.legacy.papers.deleted, env DELETED_GS_URL).

TODO: the Perl script also looked for cross-list placeholder files
(ftp/*/papers/<yymm>/<archive><num>.abs). None were found in the bucket
(sampled 2026-09), so that check was not ported.
"""

import argparse

from arxiv.legacy.papers.deleted import get_deleted_data
from sqlalchemy import bindparam, text

from ..core import CRON_ERRORS_ADDRESS, Context, Report
from ..papers import paper_key


def add_args(p: argparse.ArgumentParser) -> None:
    pass


def run(ctx: Context, args: argparse.Namespace) -> Report:
    report = Report("Deleted papers check", CRON_ERRORS_ADDRESS)
    deleted = sorted(get_deleted_data())
    store = ctx.store
    for pid in deleted:
        abs_obj = store.get(paper_key("ftp", pid, "abs"))
        if abs_obj is None or abs_obj.size != 0:
            report.problem(f"{pid}: abs {paper_key('ftp', pid, 'abs')} doesn't exist or is not zero size")
        gz = store.get(paper_key("ftp", pid, "gz"))
        if gz is None or gz.size == 0:
            if store.get(paper_key("ftp", pid, "tar.gz")):
                report.problem(f"{pid}: tar.gz {paper_key('ftp', pid, 'tar.gz')} exists in place of gz")
            else:
                report.problem(f"{pid}: gz {paper_key('ftp', pid, 'gz')} doesn't exist or is zero size")

    with ctx.engine.connect() as conn:
        for table in ("arXiv_documents", "arXiv_metadata"):
            q = text(f"SELECT paper_id, COUNT(*) FROM {table} WHERE paper_id IN :ids GROUP BY paper_id").bindparams(
                bindparam("ids", expanding=True)
            )
            for pid, n in conn.execute(q, {"ids": deleted}):
                report.problem(f"{pid}: unexpected matching row ({n}) in {table} table")

    report.info(f"Checked {len(deleted)} deleted papers, {report.problems} warnings.")
    return report
