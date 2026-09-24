"""Settings, shared context, reports and mail delivery."""

import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from functools import cached_property
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

from arxiv_functions.config import FunctionConfig
from sqlalchemy import Engine, create_engine

from .store import GcsStore, LocalStore, Store

logger = logging.getLogger(__name__)

# Default recipients, as in arxiv-bin dotfiles/nexus2.crontab
SHERIFF_ADDRESS = "sheriff@arxiv.org"
SYSTEM_QUEUE_ADDRESS = "system-queue@arxiv.org"
CRON_ERRORS_ADDRESS = "cron-errors@arxiv.org"  # the crontab's MAILTO
DB_STATS_ADDRESSES = "mod-admin@arxiv.org,db-stats-list@arxiv.org"

# The classic DB stores naive local datetimes.
DB_TZ = ZoneInfo("America/New_York")


class Settings(FunctionConfig):
    """Read from the environment (and .env). Secrets are injected as env vars
    or mounted files by Cloud Run from Secret Manager."""

    env: str = "PRODUCTION"

    # DB: SQLAlchemy URI, e.g. mysql://user:pass@host/arXiv. In Cloud Run it comes
    # from the read-only DB URI secret.
    db_url: str | None = None

    # Files: the bucket, or a local directory with the same layout
    bucket: str = "arxiv-production-data"
    local_data_dir: str | None = None

    # Mail, same contract as publish.git/arxiv-mail-sender: SMTP_URI holds the
    # HALON_CREDS secret value, smtps://user:password@host:port
    mail_dry_run: bool = True
    smtp_uri: str | None = None
    mail_from: str = "cloudcron@arxiv.org"

    workers: int = 32


@dataclass
class Report:
    subject: str
    to: str
    lines: list[str] = field(default_factory=list)
    problems: int = 0
    always_send: bool = False  # periodic reports send even with no problems

    def problem(self, line: str) -> None:
        self.lines.append(line)
        self.problems += 1

    def info(self, line: str = "") -> None:
        self.lines.append(line)

    @property
    def body(self) -> str:
        return "\n".join(self.lines) + "\n"


class Context:
    def __init__(self, settings: Settings):
        self.settings = settings

    @cached_property
    def engine(self) -> Engine:
        if not self.settings.db_url:
            raise RuntimeError("No database configured: set DB_URL")
        # recycle before Cloud SQL's idle timeout, as arxiv_functions.utils does
        return create_engine(self.settings.db_url, pool_recycle=300, pool_pre_ping=True)

    @cached_property
    def store(self) -> Store:
        if self.settings.local_data_dir:
            return LocalStore(self.settings.local_data_dir)
        return GcsStore(self.settings.bucket, connections=self.settings.workers)

    @staticmethod
    def db_now() -> datetime:
        """Now as a naive DB-local datetime, for comparing with DATETIME columns."""
        return datetime.now(DB_TZ).replace(tzinfo=None)

    def db_days_ago(self, days: float) -> datetime:
        return self.db_now() - timedelta(days=days)


def send_mail(settings: Settings, to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="arxiv.org")
    msg.set_content(body)

    if settings.mail_dry_run:
        logger.info("MAIL_DRY_RUN: not sending '%s' to %s", subject, to)
        return
    if not settings.smtp_uri:
        raise RuntimeError("SMTP_URI must be set when MAIL_DRY_RUN=false")

    uri = urlparse(settings.smtp_uri)
    if not uri.hostname:
        raise RuntimeError("SMTP_URI must include a hostname")
    smtp_cls = smtplib.SMTP_SSL if uri.scheme == "smtps" else smtplib.SMTP
    with smtp_cls(uri.hostname, uri.port or 0, timeout=30) as smtp:
        if uri.scheme == "smtp+starttls":
            smtp.starttls()
        if uri.username:
            smtp.login(unquote(uri.username), unquote(uri.password or ""))
        smtp.send_message(msg)
    logger.info("Sent '%s' to %s", subject, to)
