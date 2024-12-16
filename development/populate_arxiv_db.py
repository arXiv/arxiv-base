#!/usr/bin/python3
"""
Create the db schema from arxiv/db/models.py

NOTE: This does not work as the db/models is not fully expressing the original schema and thus
it cannot satisfy the database constraints.

The code exists for more of less for the referencing purpose.
If one day, if we ditch the tests using sqlite3 and always use mysql, we can ues MySQL
data types instead of generic Python types and this would work.

"""
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
import time
import shlex
import argparse

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
    mysql_image = "mysql:5.7.20"

    subprocess.run(["docker", "pull", mysql_image], check=True)

    subprocess.run(["docker", "rm", container_name], check=False)

    argv = [
        "docker", "run", "-d", "--name", container_name,
        "-e", "MYSQL_ROOT_PASSWORD=testpassword",
        "-e", "MYSQL_USER=testuser",
        "-e", "MYSQL_PASSWORD=testpassword",
        "-e", "MYSQL_DATABASE=" + db_name,
        "-p", f"{port}:3306",
        mysql_image
    ]

    try:
        subprocess.run(argv, check=True)
        logging.info("MySQL Docker container started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}\n\n{shlex.join(argv)}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}\n\n{shlex.join(argv)}")



    ping = ["mysql"] + conn_argv + [db_name]
    logger.info(shlex.join(ping))
    
    for _ in range(20):
        try:
            mysql = subprocess.Popen(ping, encoding="utf-8", stdin=subprocess.PIPE)
            mysql.communicate("select 1")
            if mysql.returncode == 0:
                break
        except Exception as e:
            print(e)
            pass
        time.sleep(1)


def wait_for_mysql_docker(ping):
    logger = logging.getLogger()
    
    for _ in range(20):
        try:
            mysql = subprocess.Popen(ping, encoding="utf-8", stdin=subprocess.PIPE)
            mysql.communicate("select 1")
            if mysql.returncode == 0:
                break
        except Exception as e:
            print(e)
            pass
        time.sleep(1)

        
def main(mysql_port, db_name, root_password="rootpassword") -> None:
    logger = logging.getLogger()
    conn_argv = [f"--port={mysql_port}", "-h", "127.0.0.1", "-u", "root", f"--password={root_password}",
                 # "--ssl-mode=DISABLED"
                 ]

    if not is_port_open("127.0.0.1", mysql_port):
        run_mysql_container(mysql_port, container_name="schema-creation-test-arxiv-db", db_name=db_name)

    ping = ["mysql"] + conn_argv + [db_name]
    logger.info(shlex.join(ping))
    wait_for_mysql_docker(ping)


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
        subprocess.run(["mysqldump"] + conn_argv + ["--no-data", db_name],
                       stdout=sql_file, check=True)
        

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="populate database schema")

    # Add arguments for db_name and db_port
    parser.add_argument(
        "--db_name",
        type=str,
        default="testdb",
        help="The name of the database",
    )
    parser.add_argument(
        "--db_port",
        type=int,
        default="3306",
        help="The port number for the database",
    )

    parser.add_argument(
        "--root_password",
        type=str,
        default="rootpassword",
        help="Root password",
    )

    args = parser.parse_args()
    db_port = int(args.db_port)
    db_name = args.db_name

    logger.info("port : %s name: %s", db_port, db_name)
    main(db_port, db_name, root_password=args.root_password)
