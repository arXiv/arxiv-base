"""User is attempting login with username+password."""
import pytest
from pytz import timezone
from sqlalchemy.orm import Session

from arxiv.db import models

from .util import SetUpUserMixin
from .. import authenticate, exceptions

EASTERN = timezone('US/Eastern')


def test_no_username(app):
    """Username is not entered."""
    username = ''
    password = 'foopass'
    with pytest.raises(exceptions.AuthenticationFailed):
        with app.app_context():
            authenticate.authenticate(username, password)


def test_no_password(app):
    """Password is not entered."""
    username = 'foouser'
    password = ''
    with pytest.raises(exceptions.AuthenticationFailed):
        with app.app_context():
            authenticate.authenticate(username, password)


def test_password_is_incorrect(app):
    """Password is incorrect."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('foouser', 'notthepassword')


def test_password_is_correct(app, foouser):
    """Password is correct."""
    with app.app_context():
        user, auths = authenticate.authenticate(foouser.tapir_nicknames.nickname, foouser.tapir_passwords.test_only_password)
        assert isinstance(user, authenticate.domain.User)
        assert isinstance(auths, authenticate.domain.Authorizations)
        assert user.user_id == foouser.user_id  #User ID is set correctly
        assert user.username == foouser.tapir_nicknames.nickname  #Username is set correctly
        assert user.email == foouser.email  #User email is set correctly
        assert auths.classic == 6  #Authorizations are set


def test_login_with_email_and_correct_password(app, foouser):
    """User attempts to log in with e-mail address."""
    with app.app_context():
        user, auths = authenticate.authenticate(foouser.email,
                                                foouser.tapir_passwords.test_only_password)
        assert isinstance(user, authenticate.domain.User)
        assert isinstance(auths, authenticate.domain.Authorizations)
        assert user.user_id == foouser.user_id  #User ID is set correctly
        assert user.username == foouser.tapir_nicknames.nickname  #Username is set correctly
        assert user.email == foouser.email  #User email is set correctly
        assert auths.classic == 6  #authorizations are set


def test_no_such_user(app):
    """Username does not exist."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('nobody', 'thepassword')


def test_bad_data(app):
    """Test with bad data."""
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('abc', '')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('abc', 234)
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('abc', 'β')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('', 'password')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('β', 'password')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate('long' * 100, 'password')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(1234, 'password')

        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, 'abcc-something')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, '-something')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, ('long' * 20) + '-something')
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(None, None, '1234-' + 40 * 'long')


def test_values_that_arent_strings_are_refused_as_such():
    """The checks name the type they were passed, and the username's checks the username."""
    with pytest.raises(ValueError, match="non-str password: <class 'int'>"):
        authenticate._authenticate_password('abc', 234)
    with pytest.raises(ValueError, match="non-str username_or_email: <class 'int'>"):
        authenticate._authenticate_password(1234, 'password')


@pytest.mark.parametrize('name', ['nobody', 'nobody@example.org'])
def test_an_unknown_name_hashes_the_password_too(app, mocker, name):
    """No account: the password is checked against a stand-in hash, as a wrong password would be."""
    check = mocker.patch.object(authenticate, 'check_password', wraps=authenticate.check_password)
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(name, 'thepassword')
    check.assert_called_once_with('thepassword', authenticate._NO_ACCOUNT_HASH)


def test_an_account_that_cant_log_in_hashes_the_password_too(app, db_with_user, mocker, foouser):
    """A banned account, and an account with no password row."""
    with Session(db_with_user) as session:
        session.query(models.TapirUser).filter(models.TapirUser.user_id == foouser.user_id) \
            .update({models.TapirUser.flag_banned: 1})
        session.add(models.TapirUser(
            user_id=15831, first_name='no', last_name='password', suffix_name='', email='nopw@last.iv',
            policy_class=2, flag_edit_users=0, flag_email_verified=1, flag_edit_system=0, flag_approved=1,
            flag_deleted=0, flag_banned=0, tracking_cookie='nopwcookie'))
        session.add(models.TapirNickname(
            nickname='nopwuser', user_id=15831, user_seq=1, flag_valid=1, role=0, policy=0, flag_primary=1))
        session.commit()
    check = mocker.patch.object(authenticate, 'check_password', wraps=authenticate.check_password)
    with app.app_context():
        for name in (foouser.tapir_nicknames.nickname, 'nopwuser', 'nopw@last.iv'):
            with pytest.raises(exceptions.AuthenticationFailed):
                authenticate.authenticate(name, 'thepassword')
    assert check.call_args_list == [mocker.call('thepassword', authenticate._NO_ACCOUNT_HASH)] * 3


def test_a_wrong_password_is_checked_against_the_accounts_hash(app, mocker, foouser):
    check = mocker.patch.object(authenticate, 'check_password', wraps=authenticate.check_password)
    with app.app_context():
        with pytest.raises(exceptions.AuthenticationFailed):
            authenticate.authenticate(foouser.tapir_nicknames.nickname, 'notthepassword')
    check.assert_called_once_with('notthepassword', foouser.tapir_passwords.password_enc)
