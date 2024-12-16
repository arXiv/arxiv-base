import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, UTC

import pytest
from flask import Flask
from sqlalchemy import create_engine, NullPool, text, CursorResult
from sqlalchemy.orm import Session

from arxiv.auth.auth import Auth
from arxiv.auth.auth.middleware import AuthMiddleware

from arxiv.auth.legacy import util
from arxiv.auth.legacy.passwords import hash_password
from arxiv.base import Base
from arxiv.base.middleware import wrap
from arxiv.db import models, Session as arXiv_session
from arxiv.db.models import configure_db_engine

PYTHON_EXE = "python"
DB_PORT = 25336
DB_NAME = "testdb"
ROOT_PASSWORD = "rootpassword"
my_sql_cmd = ["mysql", f"--port={DB_PORT}", "-h", "127.0.0.1", "-u", "root", f"--password={ROOT_PASSWORD}"]


def arxiv_base_dir() -> str:
    """
    Returns:
    "arxiv-base" directory abs path
    """
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def db_uri(request):
    db_type = request.config.getoption("--db")

    if db_type == "sqlite":
        # db_path = tempfile.mkdtemp()
        # uri = f'sqlite:///{db_path}/test.db'
        uri = f'sqlite'
    elif db_type == "mysql":
        # load_arxiv_db_schema.py sets up the docker and load the db schema
        loader_py = os.path.join(arxiv_base_dir(), "development", "load_arxiv_db_schema.py")
        subprocess.run(["poetry", "run", PYTHON_EXE, loader_py, f"--db_name={DB_NAME}", f"--db_port={DB_PORT}",
                        f"--root_password={ROOT_PASSWORD}"], encoding="utf-8", check=True)
        uri = f"mysql://testuser:testpassword@127.0.0.1:{DB_PORT}/{DB_NAME}"
    else:
       raise ValueError(f"Unsupported database dialect: {db_type}")

    yield uri


@pytest.fixture(scope="function")
def classic_db_engine(db_uri):
    logger = logging.getLogger()
    db_path = None
    use_ssl = False
    if db_uri.startswith("sqlite"):
        db_path = tempfile.mkdtemp()
        uri = f'sqlite:///{db_path}/test.db'
        db_engine = create_engine(uri)
        util.create_arxiv_db_schema(db_engine)
    else:
        conn_args = {}
        if not use_ssl:
            conn_args["ssl"] = None
        db_engine = create_engine(db_uri, connect_args=conn_args, poolclass=NullPool)

        # Clean up the tables to real fresh
        targets = []
        with db_engine.connect() as connection:
            tables = [row[0] for row in connection.execute(text("SHOW TABLES"))]
            for table_name in tables:
                counter: CursorResult = connection.execute(text(f"select count(*) from {table_name}"))
                count = counter.first()[0]
                if count and int(count):
                    targets.append(table_name)
            connection.invalidate()

        if targets:
            if len(targets) > 20 or "arXiv_metadata" in targets:
                logger.error("Too many tables used in the database. Suspect this is not the intended test database.\n"
                             "Make sure you are not using any of production or even development database.")
                exit(1)
            statements = [ "SET FOREIGN_KEY_CHECKS = 0;"] + [f"TRUNCATE TABLE {table_name};" for table_name in targets] + ["SET FOREIGN_KEY_CHECKS = 1;"]
            # debug_sql = "SHOW PROCESSLIST;\nSELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;\n"
            sql = "\n".join(statements)
            cmd = my_sql_cmd
            if not use_ssl:
                cmd = my_sql_cmd + ["--ssl-mode=DISABLED"]
            cmd = cmd + [DB_NAME]
            mysql = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, encoding="utf-8")
            try:
                # logger.info(sql)
                out, err = mysql.communicate(sql, timeout=9999)
                if out:
                    logger.info(out)
                if err and not err.startswith("[Warning] Using a password on the command line interface can be insecure"):
                    logger.info(err)
            except Exception as exc:
                logger.error(f"BOO: {str(exc)}", exc_info=True)

    util.bootstrap_arxiv_db(db_engine)

    yield db_engine

    if db_path:
        shutil.rmtree(db_path)
    # else:
    #     # This is to shut down the client connection from the database side. Get the list of processes used by
    #     # the testuser and kill them all.
    #     with db_engine.connect() as connection:
    #         danglings: CursorResult = connection.execute(text("select id from information_schema.processlist where user = 'testuser';")).all()
    #         connection.invalidate()
    #     if danglings:
    #         kill_conn = "\n".join([ f"kill {id[0]};" for id in danglings ])
    #         cmd = my_sql_cmd
    #         if not use_ssl:
    #             cmd = cmd + ["--ssl-mode=DISABLED"]
    #         cmd = cmd + [DB_NAME]
    #         mysql = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, encoding="utf-8")
    #         mysql.communicate(kill_conn)
    db_engine.dispose()


@pytest.fixture
def foouser(mocker):
    user_id = '15830'
    email = 'first@last.iv'
    # Why does this use a mock for the use and not a models.TapirUser?
    # Using an ORM obj caused problems when outside a session, but it seems
    # like there should be a way to do that.
    user = mocker.MagicMock(
        user_id=user_id,
        first_name='first',
        last_name='last',
        suffix_name='iv',
        email=email,
        policy_class=2,
        flag_edit_users=1,
        flag_email_verified=1,
        flag_edit_system=0,
        flag_approved=1,
        flag_deleted=0,
        flag_banned=0,
        tracking_cookie='foocookie',
    )
    nick = mocker.MagicMock(
        nickname='foouser',
        user_id=user_id,
        user_seq=1,
        flag_valid=1,
        role=0,
        policy=0,
        flag_primary=1
    )
    password = 'thepassword'
    hashed = hash_password(password)
    password = mocker.MagicMock(
        user_id=user_id,
        password_storage=2,
        password_enc=hashed,
        test_only_password=password,  # this is not on the real obj, just used so tests have access to it
    )
    n = util.epoch(datetime.now(tz=UTC))
    secret = 'foosecret'
    token = mocker.MagicMock(
        user_id=user_id,
        secret=secret,
        valid=1,
        issued_when=n,
        issued_to='127.0.0.1',
        remote_host='foohost.foo.com',
        session_id=1
    )
    user.tapir_nicknames = nick
    user.tapir_passwords = password
    user.tapir_tokens = token

    return user


@pytest.fixture
def db_with_user(classic_db_engine, foouser):
    try:
        _load_test_user(classic_db_engine, foouser)
    except Exception as e:
        pass
    yield classic_db_engine


def _load_test_user(db_engine, foouser):
    # just combines db_engine and foouser
    with Session(db_engine) as session:

        user = models.TapirUser(
            user_id=foouser.user_id,
            first_name=foouser.first_name,
            last_name=foouser.last_name,
            suffix_name=foouser.suffix_name,
            email=foouser.email,
            policy_class=foouser.policy_class,
            flag_edit_users=foouser.flag_edit_users,
            flag_email_verified=foouser.flag_email_verified,
            flag_edit_system=foouser.flag_edit_system,
            flag_approved=foouser.flag_approved,
            flag_deleted=foouser.flag_deleted,
            flag_banned=foouser.flag_banned,
            tracking_cookie=foouser.tracking_cookie,
        )
        session.add(user)
        session.commit()

        # Make sure the ID is correct. If you are using mysql with different auto-increment. you may get an different id
        # However, domain.User's user_id is str, and the db/models User model user_id is int.
        # wish they match but since tapir's user id came from auto-increment id which has to be int, I guess
        # "it is what it is".
        assert str(foouser.user_id) == str(user.user_id)

        nick = models.TapirNickname(
            nickname=foouser.tapir_nicknames.nickname,
            user_id=foouser.tapir_nicknames.user_id,
            user_seq=foouser.tapir_nicknames.user_seq,
            flag_valid=foouser.tapir_nicknames.flag_valid,
            role=foouser.tapir_nicknames.role,
            policy=foouser.tapir_nicknames.policy,
            flag_primary=foouser.tapir_nicknames.flag_primary,
        )
        session.add(nick)
        session.commit()

        password = models.TapirUsersPassword(
            user_id=foouser.user_id,
            password_storage=foouser.tapir_passwords.password_storage,
            password_enc=foouser.tapir_passwords.password_enc,
        )
        session.add(password)
        session.commit()

    with Session(db_engine) as session:
        tapir_session_1 = models.TapirSession(
            session_id = foouser.tapir_tokens.session_id,
            user_id = foouser.user_id,
            last_reissue = 0,
            start_time = 0,
            end_time = 0
        )
        session.add(tapir_session_1)
        session.commit()
        assert foouser.tapir_tokens.session_id == tapir_session_1.session_id

    with Session(db_engine) as session:
        token = models.TapirPermanentToken(
            user_id=foouser.user_id,
            secret=foouser.tapir_tokens.secret,
            valid=foouser.tapir_tokens.valid,
            issued_when=foouser.tapir_tokens.issued_when,
            issued_to=foouser.tapir_tokens.issued_to,
            remote_host=foouser.tapir_tokens.remote_host,
            session_id=foouser.tapir_tokens.session_id,
        )
        session.add(token)
        session.commit()


@pytest.fixture
def db_configed(db_with_user):
    db_engine, _ = configure_db_engine(db_with_user,None)
    yield None
    arXiv_session.remove()


@pytest.fixture
def app(db_with_user):
    app = Flask('test_auth_app')

    engine, _ = configure_db_engine(db_with_user, None)
    Base(app)
    Auth(app)
    wrap(app, [AuthMiddleware])
    yield app


@pytest.fixture
def request_context(app):
    yield app.test_request_context()


def pytest_addoption(parser):
    parser.addoption("--db", action="store", default="sqlite",
                     help="Database type to test against (sqlite/mysql)")
