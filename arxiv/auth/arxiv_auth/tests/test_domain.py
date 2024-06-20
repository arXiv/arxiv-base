"""Tests for :mod:`arxiv.users.domain`."""

from unittest import TestCase
from datetime import datetime
from arxiv.taxonomy import definitions
from pytz import timezone
from arxiv.auth.arxiv_auth.auth import scopes
from arxiv.auth.arxiv_auth import domain

EASTERN = timezone('US/Eastern')


class TestSession(TestCase):
    def test_with_session(self):
        session = domain.Session(
            session_id='asdf1234',
            start_time=datetime.now(), end_time=datetime.now(),
            user=domain.User(
                user_id='12345',
                email='foo@bar.com',
                username='emanresu',
                name=domain.UserFullName(forename='First', surname='Last', suffix='Lastest'),
                profile=domain.UserProfile(
                    affiliation='FSU',
                    rank=3,
                    country='us',
                    default_category=definitions.CATEGORIES['astro-ph.CO'],
                    submission_groups=['grp_physics']
                )
            ),
            authorizations=domain.Authorizations(
                scopes=[scopes.VIEW_SUBMISSION, scopes.CREATE_SUBMISSION],
                endorsements=[definitions.CATEGORIES['astro-ph.CO']]
            )
        )
        session_data = session.dict()
        self.assertEqual(session_data['authorizations']['scopes'],
                         ['submission:read','submission:create'])

        self.assertEqual(session_data['authorizations']['endorsements'][0]['id'],
                         'astro-ph.CO')

        self.assertEqual(session_data['user']['profile']['affiliation'], 'FSU')
        self.assertEqual(session_data['user']['profile']['country'], 'us')
        self.assertEqual(session_data['user']['profile']['submission_groups'], ['grp_physics'])
        self.assertEqual(session_data['user']['profile']['default_category']['id'], 'astro-ph.CO')
        self.assertEqual(
            session_data['user']['name'],
            {'forename': 'First', 'surname': 'Last', 'suffix': 'Lastest'}
        )

        as_session = domain.session_from_dict(session_data)
        self.assertEqual(session, as_session)
