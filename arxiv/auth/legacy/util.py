"""Helpers and Flask application integration."""

from typing import Generator, List, Any
from datetime import datetime
from pytz import timezone, UTC
from contextlib import contextmanager
import logging

from flask import Flask
from sqlalchemy import text, Engine
from sqlalchemy.orm.session import Session

from arxiv.base.globals import get_application_config

from ..auth import scopes
from .. import domain
from arxiv.db import session, Base, transaction
from arxiv.db.models import TapirUser, TapirPolicyClass

EASTERN = timezone('US/Eastern')
logger = logging.getLogger(__name__)
logger.propagate = False


def now() -> int:
    """Get the current epoch/unix time."""
    return epoch(datetime.now(tz=UTC))


def epoch(t: datetime) -> int:
    """Convert a :class:`.datetime` to UNIX time."""
    delta = t - datetime.fromtimestamp(0, tz=EASTERN)
    return int(round((delta).total_seconds()))


def from_epoch(t: int) -> datetime:
    """Get a :class:`datetime` from an UNIX timestamp."""
    return datetime.fromtimestamp(t, tz=EASTERN)


def create_all(engine: Engine) -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
    with transaction() as session:
        data = session.query(TapirPolicyClass).all()
        if data:
            return

        for datum in TapirPolicyClass.POLICY_CLASSES:
            session.add(TapirPolicyClass(**datum))
        session.commit()

def drop_all(engine: Engine) -> None:
    """Drop all tables in the database."""
    Base.metadata.drop_all(engine)


def compute_capabilities(tapir_user: TapirUser) -> int:
    """Calculate the privilege level code for a user."""
    return int(sum([2 * tapir_user.flag_edit_users,
                    4 * tapir_user.flag_email_verified,
                    8 * tapir_user.flag_edit_system]))


def get_scopes(db_user: TapirUser) -> List[domain.Scope]:
    """Generate a list of authz scopes for a legacy user based on class."""
    if db_user.policy_class == TapirPolicyClass.PUBLIC_USER:
        return scopes.GENERAL_USER
    if db_user.policy_class == TapirPolicyClass.ADMIN:
        return scopes.ADMIN_USER
    return []


def is_configured() -> bool:
    """Determine whether or not the legacy auth is configured of the `Flask` app."""
    config = get_application_config()
    return not bool(missing_configs(config))

def missing_configs(config) -> List[str]:
    """Returns missing keys for configs  needed in `Flask.config` for legacy auth to work."""
    missing = [key for key in ['CLASSIC_SESSION_HASH', 'SESSION_DURATION', 'CLASSIC_COOKIE_NAME']
               if key not in config]
    return missing

def get_session_hash() -> str:
    """Get the legacy hash secret."""
    config = get_application_config()
    session_hash: str = config['CLASSIC_SESSION_HASH']
    return session_hash


def get_session_duration() -> int:
    """Get the session duration from the config."""
    config = get_application_config()
    timeout: str = config['SESSION_DURATION']
    return int(timeout)


def is_available(**kwargs: Any) -> bool:
    """Check our connection to the database."""
    try:
        session.query("1").from_statement(text("SELECT 1")).all()
    except Exception as e:
        logger.error('Encountered an error talking to database: %s', e)
        return False
    return True
