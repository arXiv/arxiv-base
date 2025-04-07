"""Tests for :mod:`arxiv.users.legacy.endorsements` using a live test DB."""

import shutil
import tempfile
from unittest import TestCase
from datetime import datetime
from pytz import timezone, UTC
import pytest

from flask import Flask
from mimesis import Person, Internet, Datetime
from sqlalchemy import insert

import arxiv.db
from arxiv.taxonomy import definitions
from arxiv.config import Settings
from arxiv.db import models, transaction
from .. import endorsements, util
from ... import domain

EASTERN = timezone('US/Eastern')


class TestEndorsement(TestCase):
    """Tests for :func:`get_endorsements`."""

    def setUp(self):
        """Generate some fake data."""
        self.app = Flask('test')
        self.db_path = tempfile.mkdtemp()
        self.app.config['CLASSIC_DATABASE_URI'] = f'sqlite:///{self.db_path}/test.db'
        self.app.config['CLASSIC_SESSION_HASH'] = 'foohash'
        settings = Settings(
                        CLASSIC_DB_URI=self.app.config['CLASSIC_DATABASE_URI'],
                        LATEXML_DB_URI=None)

        arxiv.db.init(settings)
        util.create_all(arxiv.db._classic_engine)

        self.default_tracking_data = {
            'remote_addr': '0.0.0.0',
            'remote_host': 'foo-host.foo.com',
            'tracking_cookie': '0',
            'date': '2024-01-01',
            'flag_auto': 1,
            'added_by': 1,
        }

        with self.app.app_context():
            with transaction() as session:
                person = Person('en')
                net = Internet()
                ip_addr = net.ip_v4()
                email = "foouser@agu.org"
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
                session.commit()
                session.refresh(db_user)

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

            ok_patterns = ['%w3.org', '%aaas.org', '%agu.org', '%ams.org']
            bad_patterns = ['%.com', '%.net', '%.biz.%']

            with transaction() as session:
                for pattern in ok_patterns:
                    session.execute(
                        insert(models.t_arXiv_white_email)
                        .values(pattern=str(pattern))
                    )
                for pattern in bad_patterns:
                    session.execute(
                        insert(models.t_arXiv_black_email)
                        .values(pattern=str(pattern))
                    )

                # session.add(models.EndorsementDomain(
                #     endorsement_domain='test_domain',
                #     endorse_all='n',
                #     mods_endorse_all='n',
                #     endorse_email='y',
                #     papers_to_endorse=3
                # ))

                # for category, definition in definitions.CATEGORIES_ACTIVE.items():
                #     if '.' in category:
                #         archive, subject_class = category.split('.', 1)
                #     else:
                #         archive, subject_class = category, ''
                #     session.add(models.Category(
                #         archive=archive,
                #         subject_class=subject_class,
                #         definitive=1,
                #         active=1,
                #         endorsement_domain='test_domain'
                #     ))

    def tearDown(self):
        shutil.rmtree(self.db_path)

    @pytest.mark.skipif(lambda request: request.config.getoption("--db") == "mysql",
                            reason="is set up for sqlite3 only")
    def test_get_endorsements(self):
        """Test :func:`endoresement.get_endorsements`."""
        with self.app.app_context():
            # with transaction() as session:
            #     for category, definition in definitions.CATEGORIES_ACTIVE.items():
            #             if '.' in category:
            #                 archive, subject_class = category.split('.', 1)
            #             else:
            #                 archive, subject_class = category, ''
            #             session.add(models.Category(
            #                 archive=archive,
            #                 subject_class=subject_class,
            #                 definitive=1,
            #                 active=1,
            #                 endorsement_domain='test_domain'
            #             ))
            all_endorsements = set(
                endorsements.get_endorsements(self.user)
            )
            all_possible = set(definitions.CATEGORIES_ACTIVE.values())
            self.assertEqual(all_endorsements, all_possible)

