"""Helpers and utilities for :mod:`arxiv.users`."""

import os
from typing import List
from pytz import timezone, UTC
import uuid
from datetime import timedelta, datetime
from . import auth, domain
from arxiv.base.globals import get_application_config
from arxiv.taxonomy.definitions import CATEGORIES


def generate_token(user_id: str, email: str, username: str,
                   first_name: str = 'Jane', last_name: str = 'Doe',
                   suffix_name: str = 'IV',
                   affiliation: str = 'Cornell University',
                   rank: int = 3,
                   country: str = 'us',
                   default_category: domain.Category = CATEGORIES['astro-ph.GA'],
                   submission_groups: str = 'grp_physics',
                   endorsements: List[domain.Category] = [],
                   scope: List[domain.Scope] = [],
                   verified: bool = False) -> str:
    """Generate an auth token for dev/testing purposes."""
    # Specify the validity period for the session.
    start = datetime.now(tz=timezone('US/Eastern'))
    end = start + timedelta(seconds=36000)   # Make this as long as you want.

    # Create a user with endorsements in astro-ph.CO and .GA.
    session = domain.Session(
        session_id=str(uuid.uuid4()),
        start_time=start, end_time=end,
        user=domain.User(
            user_id=user_id,
            email=email,
            username=username,
            name=domain.UserFullName(forename=first_name, surname=last_name, suffix=suffix_name),
            profile=domain.UserProfile(
                affiliation=affiliation,
                rank=int(rank),
                country=country,
                default_category=default_category,
                submission_groups=submission_groups.split(',')
            ),
            verified=verified
        ),
        authorizations=domain.Authorizations(scopes=scope,
                                             endorsements=endorsements)
    )
    token = auth.tokens.encode(session, get_application_config()['JWT_SECRET'])
    return token
