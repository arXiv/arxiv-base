"""Tests for :mod:`arxiv.users.legacy.accounts`."""
import pytest

from arxiv.taxonomy import definitions
from arxiv.db import transaction
from arxiv.db import models

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



def test_with_nonexistant_user_w_app(app):
    """There is no user with the passed username."""
    with app.app_context():
            assert not accounts.does_username_exist('baruser')

def test_with_nonexistant_user_wo_app(db_configed):
    """There is no user with the passed username."""
    assert not accounts.does_username_exist('baruser')

def test_with_existant_user_w_app(app):
    """There is a user with the passed username."""
    with app.app_context():
        assert accounts.does_username_exist('foouser')

def test_with_existant_user_wo_app(db_configed):
    """There is a user with the passed username."""
    assert accounts.does_username_exist('foouser')

def test_email(app):
    """There is no user with the passed email."""
    with app.app_context():
        assert not accounts.does_email_exist('foo@bar.com')
        assert accounts.does_email_exist('first@last.iv')

def test_register_with_duplicate_username(app):
    """The username is already in the system."""
    user = domain.User(username='foouser', email='foo@bar.com')
    ip = '1.2.3.4'
    with app.app_context():
        with pytest.raises(exceptions.RegistrationFailed):
            accounts.register(user, 'apassword1', ip=ip, remote_host=ip)

    user = domain.User(username='bazuser', email='first@last.iv')
    ip = '1.2.3.4'
    with app.app_context():
        with pytest.raises(exceptions.RegistrationFailed):
            accounts.register(user, 'apassword1', ip=ip, remote_host=ip)


def test_register_with_name_details(app):
    """Registration includes the user's name."""
    name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
    user = domain.User(username='bazuser', email='new@account.edu',
                       name=name)
    ip = '1.2.3.4'
    user_id = None
    with app.app_context():
        with transaction() as session:
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            user_id = u.user_id
            db_user, db_nick, db_profile = get_user(session, u.user_id)
            assert db_user.first_name == name.forename
            assert db_user.last_name == name.surname
            assert db_user.suffix_name == name.suffix

        loaded_user = accounts.get_user_by_id(user_id)
        assert loaded_user.email == user.email

    with app.app_context() as session:
        loaded_user = accounts.get_user_by_id(user_id)
        assert loaded_user.email == user.email


def test_register_with_bare_minimum(app):
    """Registration includes only a username, name, email address, password."""
    user = domain.User(username='bazuser', email='new@account.edu',
                       name = domain.UserFullName(forename='foo', surname='user', suffix='iv'))
    ip = '1.2.3.4'

    with app.app_context():
        with transaction() as session:
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            db_user, db_nick, db_profile = get_user(session, u.user_id)

            db_user.flag_email_verified == 0
            db_nick.nickname == user.username
            db_user.email == user.email


def test_with_no_profile(app):
    """The user exists, but there is no profile."""
    name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
    user = domain.User(username='bazuser', email='new@account.edu',
                       name=name)
    ip = '1.2.3.4'

    with app.app_context():
        u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
        loaded_user = accounts.get_user_by_id(u.user_id)

    assert loaded_user.username == user.username
    assert loaded_user.email == user.email
    assert loaded_user.profile is None


def test_register_with_profile(app):
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

    with app.app_context():
        with transaction() as session:
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            db_user, db_nick, db_profile = get_user(session, u.user_id)

            assert db_profile.affiliation ==  profile.affiliation
            assert db_profile.country ==  profile.country
            assert db_profile.type ==  profile.rank
            assert db_profile.flag_group_cs ==  1
            assert db_profile.flag_group_q_bio ==  1
            assert db_profile.flag_group_physics ==  0
            assert db_profile.archive ==  'cs'
            assert db_profile.subject_class ==  'DL'

def test_can_authenticate_after_registration(app):
    """A may authenticate a bare-minimum user after registration."""
    user = domain.User(username='bazuser', email='new@account.edu',
                       name=domain.UserFullName(forename='foo', surname='user'))
    ip = '1.2.3.4'

    with app.app_context():
        with transaction() as session:
            u, _ = accounts.register(user, 'apassword1', ip=ip, remote_host=ip)
            db_user, db_nick, db_profile = get_user(session, u.user_id)
            auth_user, auths = authenticate.authenticate(
                username_or_email=user.username,
                password='apassword1'
            )
            assert str(db_user.user_id) == auth_user.user_id


def test_update_name(app):
    """The user's name is changed."""
    name = domain.UserFullName(forename='foo', surname='user', suffix='iv')
    user = domain.User(username='bazuser', email='new@account.edu',
                       name=name)
    ip = '1.2.3.4'

    with app.app_context():
        user, _ = accounts.register(user, 'apassword1', ip=ip,
                                    remote_host=ip)

    with app.app_context():
        with transaction() as session:
            updated_name = domain.UserFullName(forename='Foo',
                                            surname=name.surname,
                                            suffix=name.suffix)
            updated_user = domain.User(user_id=user.user_id,
                                    username=user.username,
                                    email=user.email,
                                    name=updated_name)

            updated_user, _ = accounts.update(updated_user)
            assert user.user_id == updated_user.user_id
            assert updated_user.name.forename == 'Foo'
            db_user, db_nick, db_profile = get_user(session, user.user_id)
            assert db_user.first_name == 'Foo'

def test_update_profile(app):
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

    with app.app_context():
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

    with app.app_context():
        with transaction() as session:
            u, _ = accounts.update(updated_user)
            db_user, db_nick, db_profile = get_user(session, u.user_id)

            assert db_profile.affiliation == updated_profile.affiliation
            assert db_profile.country == updated_profile.country
            assert db_profile.type == updated_profile.rank
            assert db_profile.flag_group_cs == 1
            assert db_profile.flag_group_q_bio == 0
            assert db_profile.flag_group_physics == 1
            assert db_profile.archive == 'cs'
            assert db_profile.subject_class == 'IR'
