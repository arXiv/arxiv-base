"""Tests for :mod:`arxiv.users.legacy.endorsements` using a live test DB."""

import os
from unittest import TestCase, mock
from datetime import datetime
from pytz import timezone, UTC

from flask import Flask
from sqlalchemy import insert
from mimesis import Person, Internet, Datetime

from arxiv.db import models
from arxiv.config import Settings
from arxiv.taxonomy import definitions
from .. import endorsements, util
from ... import domain

EASTERN = timezone('US/Eastern')


class TestAutoEndorsement(TestCase):
    """Tests for :func:`get_autoendorsements`."""

    def setUp(self):
        """Generate some fake data."""

        self.app = Flask('test')
        self.app.config['CLASSIC_SESSION_HASH'] = 'foohash'
        self.app.config['CLASSIC_COOKIE_NAME'] = 'tapir_session_cookie'
        self.app.config['SESSION_DURATION'] = '36000'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' #in memory
        settings = Settings(
                        CLASSIC_DB_URI='sqlite:///:memory:',
                        LATEXML_DB_URI=None)

        engine, _ = models.configure_db(settings)
        self.default_tracking_data = {
            'remote_addr': '0.0.0.0',
            'remote_host': 'foo-host.foo.com',
            'tracking_cookie': '0'
        }

        with self.app.app_context():
            util.create_all(engine)
            with util.transaction() as session:
                person = Person('en')
                net = Internet()
                ip_addr = net.ip_v4()
                email = person.email()
                approved = 1
                deleted = 0
                banned = 0
                first_name = person.name()
                last_name = person.surname()
                suffix_name = person.title()
                joined_date = util.epoch(
                    Datetime('en').datetime().replace(tzinfo=EASTERN)
                )
                db_user = models.TapirUser(
                    first_name=first_name,
                    last_name=last_name,
                    suffix_name=suffix_name,
                    share_first_name=1,
                    share_last_name=1,
                    email=email,
                    flag_approved=approved,
                    flag_deleted=deleted,
                    flag_banned=banned,
                    flag_edit_users=0,
                    flag_edit_system=0,
                    flag_email_verified=1,
                    share_email=8,
                    email_bouncing=0,
                    policy_class=2,  # Public user. TODO: consider admin.
                    joined_date=joined_date,
                    joined_ip_num=ip_addr,
                    joined_remote_host=ip_addr
                )
                session.add(db_user)

                self.user = domain.User(
                    user_id=str(db_user.user_id),
                    username='foouser',
                    email=db_user.email,
                    name=domain.UserFullName(
                        forename=db_user.first_name,
                        surname=db_user.last_name,
                        suffix=db_user.suffix_name
                    )
                )


    def test_invalidated_autoendorsements(self):
        """The user has two autoendorsements that have been invalidated."""
        with self.app.app_context():
            with util.transaction() as session:
                issued_when = util.epoch(
                    Datetime('en').datetime().replace(tzinfo=EASTERN)
                )
                session.add(models.Endorsement(
                    endorsee_id=self.user.user_id,
                    archive='astro-ph',
                    subject_class='CO',
                    flag_valid=0,
                    type='auto',
                    point_value=10,
                    issued_when=issued_when
                ))
                session.add(models.Endorsement(
                    endorsee_id=self.user.user_id,
                    archive='astro-ph',
                    subject_class='CO',
                    flag_valid=0,
                    type='auto',
                    point_value=10,
                    issued_when=issued_when
                ))
                session.add(models.Endorsement(
                    endorsee_id=self.user.user_id,
                    archive='astro-ph',
                    subject_class='CO',
                    flag_valid=1,
                    type='auto',
                    point_value=10,
                    issued_when=issued_when
                ))
                session.add(models.Endorsement(
                    endorsee_id=self.user.user_id,
                    archive='astro-ph',
                    subject_class='CO',
                    flag_valid=1,
                    type='user',
                    point_value=10,
                    issued_when=issued_when
                ))

            result = endorsements.invalidated_autoendorsements(self.user)
        self.assertEqual(len(result), 2, "Two revoked endorsements are loaded")

    def test_category_policies(self):
        """Load category endorsement policies from the database."""
        with self.app.app_context():
            with util.transaction() as session:
                session.add(models.Category(
                    archive='astro-ph',
                    subject_class='CO',
                    definitive=1,
                    active=1,
                    endorsement_domain='astro-ph'
                ))
                session.add(models.EndorsementDomain(
                    endorsement_domain='astro-ph',
                    endorse_all='n',
                    mods_endorse_all='n',
                    endorse_email='y',
                    papers_to_endorse=3
                ))

            policies = endorsements.category_policies()
            category = definitions.CATEGORIES['astro-ph.CO']
            self.assertIn(category, policies, "Data are loaded for categories")
            self.assertEqual(policies[category]['domain'], 'astro-ph')
            self.assertFalse(policies[category]['endorse_all'])
            self.assertTrue(policies[category]['endorse_email'])
            self.assertEqual(policies[category]['min_papers'], 3)

    def test_domain_papers(self):
        """Get the number of papers published in each domain."""
        with self.app.app_context():
            with util.transaction() as session:
                # User owns three papers.
                session.execute(
                    insert(models.t_arXiv_paper_owners)
                    .values(
                        document_id=1,
                        user_id=self.user.user_id,
                        flag_author=0,  # <- User is _not_ an author.
                        valid=1,
                        **self.default_tracking_data
                    )
                )
                session.add(models.Document(
                    document_id=1,
                    title='Foo Title',
                    submitter_email='foo@bar.baz',
                    paper_id='2101.00123',
                    dated=util.epoch(datetime.now(tz=UTC))
                ))
                session.execute(
                    insert(models.t_arXiv_in_category)
                    .values(
                        document_id=1,
                        archive='cs',
                        subject_class='DL',
                        is_primary=1
                    )
                )
                session.add(models.Category(
                    archive='cs',
                    subject_class='DL',
                    definitive=1,
                    active=1,
                    endorsement_domain='firstdomain'
                ))
                # Here's another paper.
                session.execute(
                    insert(models.t_arXiv_paper_owners)
                    .values(
                        document_id=2,
                        user_id=self.user.user_id,
                        flag_author=1,  # <- User is an author.
                        valid=1,
                        **self.default_tracking_data
                    )
                )
                session.add(models.Document(
                    document_id=2,
                    title='Foo Title',
                    submitter_email='foo@bar.baz',
                    paper_id='2101.00124',
                    dated=util.epoch(datetime.now(tz=UTC))
                ))
                session.execute(
                    insert(models.t_arXiv_in_category)
                    .values(
                        document_id=2,
                        archive='cs',
                        subject_class='IR',
                        is_primary=1
                    )
                )
                session.add(models.Category(
                    archive='cs',
                    subject_class='IR',
                    definitive=1,
                    active=1,
                    endorsement_domain='firstdomain'
                ))
                # Here's a paper for which the user is an author.
                session.execute(
                    insert(models.t_arXiv_paper_owners)
                    .values(
                        document_id=3,
                        user_id=self.user.user_id,
                        flag_author=1,
                        valid=1,
                        **self.default_tracking_data
                    )
                )
                session.add(models.Document(
                    document_id=3,
                    title='Foo Title',
                    submitter_email='foo@bar.baz',
                    paper_id='2101.00125',
                    dated=util.epoch(datetime.now(tz=UTC))
                ))
                # It has both a primary and a secondary classification.
                session.execute(
                    insert(models.t_arXiv_in_category)
                    .values(
                        document_id=3,
                        archive='astro-ph',
                        subject_class='EP',
                        is_primary=1
                    )
                )
                session.execute(
                    insert(models.t_arXiv_in_category)
                    .values(
                        document_id=3,
                        archive='astro-ph',
                        subject_class='CO',
                        is_primary=0    # <- secondary!
                    )
                )
                session.add(models.Category(
                    archive='astro-ph',
                    subject_class='EP',
                    definitive=1,
                    active=1,
                    endorsement_domain='seconddomain'
                ))
                session.add(models.Category(
                    archive='astro-ph',
                    subject_class='CO',
                    definitive=1,
                    active=1,
                    endorsement_domain='seconddomain'
                ))
            papers = endorsements.domain_papers(self.user)
            self.assertEqual(papers['firstdomain'], 2)
            self.assertEqual(papers['seconddomain'], 2)

    def test_is_academic(self):
        """Determine whether a user is academic based on email."""
        ok_patterns = ['%w3.org', '%aaas.org', '%agu.org', '%ams.org']
        bad_patterns = ['%.com', '%.net', '%.biz.%']
        with self.app.app_context():
            with util.transaction() as session:
                for pattern in ok_patterns:
                    session.execute(insert(
                        models.t_arXiv_white_email)
                        .values(pattern=str(pattern))
                    )
                for pattern in bad_patterns:
                    session.execute(insert(
                        models.t_arXiv_black_email)
                        .values(pattern=str(pattern))
                    )

            self.assertTrue(endorsements.is_academic(domain.User(
                user_id='2',
                email='someone@fsu.edu',
                username='someone'
            )))
            self.assertFalse(endorsements.is_academic(domain.User(
                user_id='2',
                email='someone@fsu.biz.edu',
                username='someone'
            )))
            self.assertTrue(endorsements.is_academic(domain.User(
                user_id='2',
                email='someone@aaas.org',
                username='someone'
            )))
            self.assertFalse(endorsements.is_academic(domain.User(
                user_id='2',
                email='someone@foo.com',
                username='someone'
            )))
