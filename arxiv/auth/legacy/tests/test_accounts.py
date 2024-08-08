"""Tests for :mod:`arxiv.users.legacy.accounts`."""

from unittest import TestCase

from arxiv.taxonomy import definitions
from arxiv.db import transaction
from arxiv.db import models
from .util import SetUpUserMixin

from .. import authenticate, exceptions
from .. import accounts
from ... import domain


def get_user(session, user_id):
    """Helper to get user database objects by user id."""
    db_user, db_nick = (
        session.query(models.TapirUser, models.TapirNickname)
        .filter(models.TapirUser.user_id == user_id)
        .filter(models.TapirNickname.flag_primary == 1)
        .filter(models.TapirNickname.user_id == models.TapirUser.user_id)
        .first()
    )

    db_profile = session.query(models.Demographic) \
        .filter(models.Demographic.user_id == user_id) \
        .first()

    return db_user, db_nick, db_profile


class TestUsernameExists(SetUpUserMixin):
    """Tests for :mod:`accounts.does_username_exist`."""

    def test_with_nonexistant_user(self):
        """There is no user with the passed username."""
        with self.app.app_context():
            self.assertFalse(accounts.does_username_exist('baruser'))

    def test_with_existant_user(self):
        """There is a user with the passed username."""
        with self.app.app_context():
            self.assertTrue(accounts.does_username_exist('foouser'))


class TestEmailExists(SetUpUserMixin):
    """Tests for :mod:`accounts.does_email_exist`."""

    def test_with_nonexistant_email(self):
        """There is no user with the passed email."""
        with self.app.app_context():
            self.assertFalse(accounts.does_email_exist('foo@bar.com'))

    def test_with_existant_email(self):
        """There is a user with the passed email."""
        with self.app.app_context():
            self.assertTrue(accounts.does_email_exist('first@last.iv'))


class TestRegister(SetUpUserMixin, TestCase):
    """Tests for :mod:`accounts.register`."""

    def test_register_with_duplicate_username(self):
        """The username is already in the system."""
        user = domain.User(username='foouser', email='foo@bar.com')
        ip = '1.2.3.4'
        with self.app.app_context():
            with self.assertRaises(exceptions.RegistrationFailed):
                accounts.register(user, 'apassword1', ip=ip, remote_host=ip)

    def test_register_with_duplicate_email(self):
        """The email address is already in the system."""
        user = domain.User(username='bazuser', email='first@last.iv')
        ip = '1.2.3.4'
        with self.app.app_context():
            with self.assertRaises(exceptions.RegistrationFailed):
                accounts.register(user, 'apassword1', ip=ip, remote_host=ip)

    def test_register_with_name_details(self):
        """Registration includes the user's name."""
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name)
        ip = '1.2.3.4'

        with self.app.app_context():
            with transaction() as session:
                u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
                db_user, db_nick, db_profile = get_user(session, u.user_id)

                self.assertEqual(db_user.first_name, name.forename)
                self.assertEqual(db_user.last_name, name.surname)
                self.assertEqual(db_user.suffix_name, name.suffix)

    def test_register_with_bare_minimum(self):
        """Registration includes only a username, name, email address, password."""
        user = domain.User(username='bazuser', email='new@account.edu',
                           name = domain.UserFullName(forename='foo', surname='user', suffix='iv'))
        ip = '1.2.3.4'

        with self.app.app_context():
            with transaction() as session:
                u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
                db_user, db_nick, db_profile = get_user(session, u.user_id)

                self.assertEqual(db_user.flag_email_verified, 0)
                self.assertEqual(db_nick.nickname, user.username)
                self.assertEqual(db_user.email, user.email)

    def test_register_with_profile(self):
        """Registration includes profile information."""
        profile = domain.UserProfile(
            affiliation='School of Hard Knocks',
            country='de',
            rank=1,
            submission_groups=['grp_cs', 'grp_q-bio'],
            default_category=definitions.CATEGORIES['cs.DL'],
            homepage_url='https://google.com'
        )
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name, profile=profile)
        ip = '1.2.3.4'

        with self.app.app_context():
            with transaction() as session:
                u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
                db_user, db_nick, db_profile = get_user(session, u.user_id)

                self.assertEqual(db_profile.affiliation, profile.affiliation)
                self.assertEqual(db_profile.country, profile.country),
                self.assertEqual(db_profile.type, profile.rank),
                self.assertEqual(db_profile.flag_group_cs, 1)
                self.assertEqual(db_profile.flag_group_q_bio, 1)
                self.assertEqual(db_profile.flag_group_physics, 0)
                self.assertEqual(db_profile.archive, 'cs')
                self.assertEqual(db_profile.subject_class, 'DL')

    def test_can_authenticate_after_registration(self):
        """A may authenticate a bare-minimum user after registration."""
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=domain.UserFullName(forename='foo', surname='user'))
        ip = '1.2.3.4'

        with self.app.app_context():
            with transaction() as session:
                u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
                db_user, db_nick, db_profile = get_user(session, u.user_id)
                auth_user, auths = authenticate.authenticate(
                    username_or_email=user.username,
                    password='apassword1'
                )
                self.assertEqual(str(db_user.user_id), auth_user.user_id)


class TestGetUserById(SetUpUserMixin):
    """Tests for :func:`accounts.get_user_by_id`."""

    def test_user_exists(self):
        """A well-rounded user exists with the requested user id."""
        profile = domain.UserProfile(
            affiliation='School of Hard Knocks',
            country='de',
            rank=1,
            submission_groups=['grp_cs', 'grp_q-bio'],
            default_category=definitions.CATEGORIES['cs.DL'],
            homepage_url='https://google.com'
        )
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name, profile=profile)
        ip = '1.2.3.4'

        with self.app.app_context():
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            loaded_user = accounts.get_user_by_id(u.user_id)

        self.assertEqual(loaded_user.username, user.username)
        self.assertEqual(loaded_user.email, user.email)
        self.assertEqual(loaded_user.profile.affiliation, profile.affiliation)

    def test_user_does_not_exist(self):
        """No user with the specified username."""
        with self.app.app_context():
            with self.assertRaises(exceptions.NoSuchUser):
                accounts.get_user_by_id('1234')

    def test_with_no_profile(self):
        """The user exists, but there is no profile."""
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name)
        ip = '1.2.3.4'

        with self.app.app_context():
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            loaded_user = accounts.get_user_by_id(u.user_id)

        self.assertEqual(loaded_user.username, user.username)
        self.assertEqual(loaded_user.email, user.email)
        self.assertIsNone(loaded_user.profile)


class TestUpdate(SetUpUserMixin, TestCase):
    """Tests for :func:`accounts.update`."""

    def test_user_without_id(self):
        """A :class:`domain.User` is passed without an ID."""
        user = domain.User(username='bazuser', email='new@account.edu')
        with self.app.app_context():
            with self.assertRaises(ValueError):
                accounts.update(user)

    def test_update_nonexistant_user(self):
        """A :class:`domain.User` is passed that is not in the database."""
        user = domain.User(username='bazuser', email='new@account.edu',
                           user_id='12345')
        with self.app.app_context():
            with self.assertRaises(exceptions.NoSuchUser):
                accounts.update(user)

    def test_update_name(self):
        """The user's name is changed."""
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name)
        ip = '1.2.3.4'

        with self.app.app_context():
            user, _ = accounts.register(user, 'apassword1', ip=ip,
                                        remote_host=ip)

        with self.app.app_context():
            with transaction() as session:
                updated_name = domain.UserFullName(forename='Foo',
                                                surname=name.surname,
                                                suffix=name.suffix)
                updated_user = domain.User(user_id=user.user_id,
                                        username=user.username,
                                        email=user.email,
                                        name=updated_name)

                updated_user, _ = accounts.update(updated_user)
                self.assertEqual(user.user_id, updated_user.user_id)
                self.assertEqual(updated_user.name.forename, 'Foo')
                db_user, db_nick, db_profile = get_user(session, user.user_id)
                self.assertEqual(db_user.first_name, 'Foo')

    def test_update_profile(self):
        """Changes are made to profile information."""
        profile = domain.UserProfile(
            affiliation='School of Hard Knocks',
            country='de',
            rank=1,
            submission_groups=['grp_cs', 'grp_q-bio'],
            default_category=definitions.CATEGORIES['cs.DL'],
            homepage_url='https://google.com'
        )
        name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
        user = domain.User(username='bazuser', email='new@account.edu',
                           name=name, profile=profile)
        ip = '1.2.3.4'

        with self.app.app_context():
            user, _ = accounts.register(user, 'apassword1', ip=ip,
                                        remote_host=ip)

        updated_profile = domain.UserProfile(
            affiliation='School of Hard Knocks',
            country='us',
            rank=2,
            submission_groups=['grp_cs', 'grp_physics'],
            default_category=definitions.CATEGORIES['cs.IR'],
            homepage_url='https://google.com'
        )
        updated_user = domain.User(user_id=user.user_id,
                                   username=user.username,
                                   email=user.email,
                                   name=name,
                                   profile=updated_profile)

        with self.app.app_context():
            with transaction() as session:
                u, _ = accounts.update(updated_user)
                db_user, db_nick, db_profile = get_user(session, u.user_id)

                self.assertEqual(db_profile.affiliation,
                                updated_profile.affiliation)
                self.assertEqual(db_profile.country, updated_profile.country),
                self.assertEqual(db_profile.type, updated_profile.rank),
                self.assertEqual(db_profile.flag_group_cs, 1)
                self.assertEqual(db_profile.flag_group_q_bio, 0)
                self.assertEqual(db_profile.flag_group_physics, 1)
                self.assertEqual(db_profile.archive, 'cs')
                self.assertEqual(db_profile.subject_class, 'IR')
