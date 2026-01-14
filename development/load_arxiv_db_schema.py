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


def main(
    mysql_port: int,
    db_name: str,
    root_password: str = "rootpassword",
    schema_sql: str = "arxiv_db_schema.sql",
    use_ssl: bool = False,
) -> None:
    logger = logging.getLogger()
    conn_argv = [
        f"--port={mysql_port}",
        "-h",
        "127.0.0.1",
        "-u",
        "root",
        f"--password={root_password}",
    ]
    if not use_ssl:
        conn_argv.append("--ssl-mode=DISABLED")

    if not is_port_open("127.0.0.1", mysql_port):
        logger.warning("Starting fake-arxiv-db")
        run_mysql_container(
            mysql_port,
            container_name="fake-arxiv-db",
            db_name=db_name,
            root_password=root_password,
        )

    cli = ["mysql"] + conn_argv + [db_name]
    for _ in range(20):
        if is_port_open("127.0.0.1", mysql_port):
            try:
                mysql = subprocess.Popen(
                    cli,
                    encoding="utf-8",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                mysql.communicate("select 1")
                container_name = "fake-arxiv-db"
                if mysql.returncode == 0:
                    sql_cmd = [
                        "docker", "exec", container_name, "mysql",
                        "-uroot", f"-p{root_password}",
                        "-e",
                        "SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';"
                    ]
                    subprocess.run(sql_cmd, check=True)
                    debug_cmd = [
                        "docker", "exec", container_name, "mysql",
                        "-uroot", f"-p{root_password}",
                        "-e", "SELECT @@sql_mode;"
                    ]
                    result = subprocess.run(debug_cmd, capture_output=True, text=True)
                    logger.info(f"Current SQL mode: {result.stdout}")
                    break
            except Exception as e:
                print(e)
                pass
        time.sleep(1)

    if not os.path.exists(schema_sql) and ("/" not in schema_sql):
        development_dir = os.path.dirname(__file__)
        arxiv_base_dir = os.path.dirname(development_dir)
        schema_sql = os.path.join(
            os.path.join(arxiv_base_dir, "arxiv", "db", schema_sql)
        )
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
    main(
        db_port,
        db_name,
        root_password=args.root_password,
        schema_sql=args.schema,
        use_ssl=args.use_ssl,
    )
