"""consistency-checks <check> [options]: run one check, print its report, and mail
it if it found problems (or always, for periodic reports).

Exit status is non-zero only if the check itself failed, so Cloud Run job
failure alerts mean "the check is broken", not "the check found something".
"""

import argparse
import logging
import sys

from arxiv_functions.utils import set_up_cloud_logging

from .checks import categories_check, db_stats, deleted_papers, new_accounts, orig_consistency, recent_articles
from .core import Context, Settings, send_mail

CHECKS = {
    "new_accounts": new_accounts,
    "db_stats": db_stats,
    "deleted_papers": deleted_papers,
    "recent_articles": recent_articles,
    "orig_consistency": orig_consistency,
    "categories": categories_check,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="consistency-checks", description=__doc__)
    sub = parser.add_subparsers(dest="check", required=True)
    for name, mod in CHECKS.items():
        p = sub.add_parser(name, help=(mod.__doc__ or "").strip().splitlines()[0])
        p.add_argument("--mail-to", help="send the report here instead of the check's default")
        p.add_argument("--no-mail", action="store_true", help="only print the report")
        p.add_argument("-v", "--verbose", action="store_true", help="send the report even with no problems")
        mod.add_args(p)
    args = parser.parse_args(argv)

    settings = Settings()
    set_up_cloud_logging(settings)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    report = CHECKS[args.check].run(Context(settings), args)
    print(report.body)
    if (report.problems or report.always_send or args.verbose) and not args.no_mail:
        send_mail(settings, args.mail_to or report.to, report.subject, report.body)
    logging.getLogger("consistency_checks").info("%s: %d problems", args.check, report.problems)
    return 0


if __name__ == "__main__":
    sys.exit(main())
