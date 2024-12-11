#!/usr/bin/python3
import os
import sys
import subprocess
import logging
import time
import shlex
import argparse

from development.run_mysql_container import is_port_open, run_mysql_container

logging.basicConfig(level=logging.INFO)

arxiv_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(arxiv_base_dir)


def main(mysql_port: int, db_name: str, root_password: str="rootpassword", schema_sql: str="arxiv_db_schema.sql",
         use_ssl: bool = False,
         ) -> None:
    conn_argv = [f"--port={mysql_port}", "-h", "127.0.0.1", "-u", "root", f"--password={root_password}"]
    if not use_ssl:
        conn_argv.append("--ssl-mode=DISABLED")

    if not is_port_open("127.0.0.1", mysql_port):
        run_mysql_container(mysql_port, container_name="fake-arxiv-db", db_name=db_name, root_password=root_password)

    cli = ["mysql"] + conn_argv + [db_name]
    for _ in range(20):
        if is_port_open("127.0.0.1", mysql_port):
            try:
                mysql = subprocess.Popen(cli, encoding="utf-8",
                                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                mysql.communicate("select 1")
                if mysql.returncode == 0:
                    break
            except Exception as e:
                print(e)
                pass
        time.sleep(1)

    if not os.path.exists(schema_sql) and ("/" not in schema_sql):
        schema_sql = os.path.join(os.path.dirname(__file__), schema_sql)
    try:
        with open(schema_sql, encoding="utf-8") as schema_file:
            subprocess.call(cli, encoding="utf-8", stdin=schema_file, timeout=60)
    except:
        logger.error("%s", shlex.join(cli), exc_info=True)
        exit(1)
    finally:
        logger.info("Finish loading schema")
    exit(0)


if __name__ == "__main__":
    """
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
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

    parser.add_argument(
        "--schema",
        type=str,
        default="arxiv_db_schema.sql",
        help="arXiv db Schema",
    )

    parser.add_argument(
        "--use_ssl",
        help="Use SSL",
        action="store_true",
    )

    args = parser.parse_args()
    db_port = int(args.db_port)
    db_name = args.db_name

    logger.info("port : %s name: %s", db_port, db_name)
    main(db_port, db_name, root_password=args.root_password, schema_sql=args.schema, use_ssl=args.use_ssl)
