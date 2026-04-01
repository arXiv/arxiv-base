"""
Minimal test for TapirEmailTemplate Utf8String and Utf8Text column types.

To run this test:
    pytest tests/test_utf8_columns.py -v

The test fixture automatically manages the Docker MySQL container.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
import socket
import subprocess
import time
from typing import Generator

import pytest
from sqlalchemy import Engine, create_engine, NullPool
from sqlalchemy.orm import Session

from arxiv.db.models import TapirEmailTemplate, AdminLog


# Test database connection parameters
DB_HOST: str = "127.0.0.1"
DB_PORT: int = 13306
DB_NAME: str = "arXiv"
DB_USER: str = "testuser"
DB_PASSWORD: str = "testpassword"

# Path to docker-compose.yml
TESTS_DIR: str = os.path.dirname(os.path.abspath(__file__))
DOCKER_COMPOSE_FILE: str = os.path.join(TESTS_DIR, "docker-compose.yml")


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0


def wait_for_mysql(host: str, port: int, user: str, password: str, db: str,
                   timeout: int = 60) -> bool:
    """Wait for MySQL to be ready to accept connections."""
    from sqlalchemy import text

    uri = f"mysql://{user}:{password}@{host}:{port}/{db}"
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            try:
                engine = create_engine(uri, poolclass=NullPool)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                engine.dispose()
                return True
            except Exception:
                pass
        time.sleep(1)
    return False


@pytest.fixture(scope="module")
def db_engine() -> Generator[Engine, None, None]:
    """Create database engine for testing.

    This fixture:
    1. Purges any existing MySQL container
    2. Starts a fresh MySQL container via docker-compose
    3. Waits for MySQL to be ready
    4. Yields the SQLAlchemy engine
    5. Cleans up the container after tests
    """
    # Purge existing container
    subprocess.run(
        ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "-v", "--remove-orphans"],
        capture_output=True,
        check=False
    )

    # Start fresh container
    result = subprocess.run(
        ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"Failed to start MySQL container: {result.stderr}")

    # Wait for MySQL to be ready
    if not wait_for_mysql(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, timeout=120):
        # Clean up on failure
        subprocess.run(
            ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "-v"],
            capture_output=True,
            check=False
        )
        pytest.fail("MySQL container did not become ready in time")

    # Create engine
    uri = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(uri, poolclass=NullPool)

    yield engine

    # Cleanup
    engine.dispose()
    subprocess.run(
        ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "-v", "--remove-orphans"],
        capture_output=True,
        check=False
    )


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    with Session(db_engine) as session:
        yield session
        session.rollback()


utf8_data: str = """
Email template with UTF-8 content:
- Japanese: こんにちは世界
"""


class TestTapirEmailTemplateUtf8:
    """Test TapirEmailTemplate with UTF-8 data in Utf8String and Utf8Text columns."""

    def test_insert_and_read_utf8_data(self, db_session: Session) -> None:
        """Test that UTF-8 characters can be stored and retrieved correctly."""
        # UTF-8 test strings including various scripts
        utf8_short_name = "test_tmpl"
        utf8_long_name = "Test Template with UTF-8: 日本語"

        # Create the template using the test_user (user_id=1)
        template = TapirEmailTemplate(
            short_name=utf8_short_name,
            lang="en",
            long_name=utf8_long_name,
            data=utf8_data,
            sql_statement="SELECT 1",
            update_date=0,
            created_by=1,  # test_user
            updated_by=1,  # test_user
            workflow_status=0,
            flag_system=0,
        )

        db_session.add(template)
        db_session.commit()

        # Refresh to get the auto-generated template_id
        db_session.refresh(template)
        template_id = template.template_id

        # Clear the session cache and re-fetch from database
        db_session.expire_all()

        # Query the template back
        fetched = db_session.get(TapirEmailTemplate, template_id)

        # Verify the UTF-8 data was stored and retrieved correctly
        assert fetched is not None
        assert fetched.data == utf8_data
        assert "こんにちは世界" in fetched.data

        # Clean up
        db_session.delete(fetched)
        db_session.commit()

    def test_utf8_boundary_characters(self, db_session: Session) -> None:
        """Test boundary UTF-8 characters (1-byte, 2-byte, 3-byte, 4-byte sequences)."""
        # 1-byte: ASCII (U+0000 to U+007F)
        # 2-byte: Latin, Greek, etc. (U+0080 to U+07FF)
        # 3-byte: CJK, etc. (U+0800 to U+FFFF)

        boundary_data = (
            "ASCII: Hello "
            "2-byte: é ñ ü ß "
            "3-byte: 日本語 "
        )

        template = TapirEmailTemplate(
            short_name="boundary",
            lang="en",
            long_name="Boundary Test",
            data=boundary_data,
            sql_statement="SELECT 1",
            update_date=0,
            created_by=1,
            updated_by=1,
            workflow_status=0,
            flag_system=0,
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        template_id = template.template_id

        db_session.expire_all()
        fetched = db_session.get(TapirEmailTemplate, template_id)

        assert fetched is not None
        assert fetched.data == boundary_data

        # Clean up
        db_session.delete(fetched)
        db_session.commit()


class TestAdminLogUtf8:

    def test_insert_and_read_utf8_data(self, db_session: Session) -> None:
        """Test that UTF-8 characters can be stored and retrieved correctly."""
        log_text = "ASCII: Hello 2-byte: é ñ ü ß 3-byte: 日本語"

        # Create the template using the test_user (user_id=1)
        timestamp = datetime.now(tz=timezone.utc)
        log_entry = AdminLog(
            logtime=timestamp.isoformat()[:24],
            created=timestamp,
            logtext=log_text,
            old_created = timestamp,
            updated=timestamp,
        )

        db_session.add(log_entry)
        db_session.commit()

        # Refresh to get the auto-generated template_id
        db_session.refresh(log_entry)
        log_id = log_entry.id

        # Clear the session cache and re-fetch from database
        db_session.expire_all()

        # Query the template back
        fetched = db_session.get(AdminLog, log_id)

        # Verify the UTF-8 data was stored and retrieved correctly
        assert fetched is not None
        assert isinstance(fetched.logtext, str)
        assert fetched.logtext == log_text

        # Clean up
        db_session.delete(fetched)
        db_session.commit()
