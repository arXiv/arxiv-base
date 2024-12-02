#!/usr/bin/python3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import tempfile
import sqlite3
import sys
import socket
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

arxiv_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(arxiv_base_dir)

# Without this import, Base.metadata does not get populated. So it may look doing nothing but do not remove this.
import arxiv.db.models

from arxiv.db import Base, LaTeXMLBase, session_factory, _classic_engine as classic_engine


def is_port_open(host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def _make_schemas(db_engine: Engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=True)
    SessionLocal.configure(bind=db_engine)
    db_session = SessionLocal(autocommit=False, autoflush=True)

    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    LaTeXMLBase.metadata.drop_all(db_engine)
    LaTeXMLBase.metadata.create_all(db_engine)

    db_session.commit()


def run_mysql_container(port: int, container_name="mysql-test", db_name="testdb"):
    """Start a mysql docker"""
    mysql_image = "mysql:5.7"
    try:
        subprocess.run(["docker", "pull", mysql_image], check=True)

        subprocess.run(
            [
                "docker", "run", "-d", "--name", container_name,
                "-e", "MYSQL_ROOT_PASSWORD=testpassword",
                "-e", "MYSQL_USER=testuser",
                "-e", "MYSQL_PASSWORD=testpassword",
                "-e", "MYSQL_DATABASE=" + db_name,
                "-p", f"{port}:3306",
                mysql_image
            ],
            check=True
        )
        logging.info("MySQL Docker container started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")



def main() -> None:
    mysql_port = 13306
    db_name = "arxiv"

    if not is_port_open("127.0.0.1", mysql_port):
        run_mysql_container(mysql_port, container_name="fake-arxiv-db", db_name=db_name)
        for _ in range(20):
            if is_port_open("127.0.0.1", mysql_port):
                break
            time.sleep(1)
            
    db_uri = f"mysql://testuser:testpassword@127.0.0.1:{mysql_port}/{db_name}"
    db_engine = create_engine(db_uri)

    for _ in range(30):
        try:
            SessionLocal = sessionmaker(autocommit=False, autoflush=True)
            SessionLocal.configure(bind=db_engine)
            db_session = SessionLocal(autocommit=False, autoflush=True)
            
            db_session.commit()
            break
        except:
            pass
        time.sleep(1)
    
    
    _make_schemas(db_engine)
    
    with open("schema-from-arxiv-db-model.sql", "w", encoding="utf-8") as sql_file:
        subprocess.run(["mysqldump", "-h", "127.0.0.1", "--port", str(mysql_port), "-u",  "root", "-ptestpassword", "--no-data", db_name],
                       stdout=sql_file, check=True)
        

if __name__ == "__main__":
    """
    """
    main()
