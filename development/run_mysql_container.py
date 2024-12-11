#!/usr/bin/python3
import os
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

def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def run_mysql_container(port: int, container_name: str ="mysql-test", db_name: str ="testdb",
                        root_password: str = "rootpassword") -> None:
    """Start a mysql docker"""
    mysql_image = "mysql:8.0.40"

    subprocess.run(["docker", "pull", mysql_image], check=True)
    # subprocess.run(["docker", "kill", container_name], check=False)
    subprocess.run(["docker", "rm", container_name], check=False)

    argv = [
        "docker", "run", "-d", "--name", container_name,
        "-e", f"MYSQL_ROOT_PASSWORD={root_password}",
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


def stop_mysql_container(port: int, container_name: str = "mysql-test") -> None:
    """Start a mysql docker"""

    subprocess.run(["docker", "kill", container_name], check=False)
    for _ in range(10):
        if not is_port_open("127.0.0.1", port):
            break


def main(mysql_port: int, db_name: str, root_password: str = "rootpassword", restart: bool = False) -> None:
    conn_argv = [f"--port={mysql_port}", "-h", "127.0.0.1", "-u", "root", f"--password={root_password}"]

    if is_port_open("127.0.0.1", mysql_port) and restart:
        stop_mysql_container(mysql_port, container_name="fake-arxiv-db")

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
                exit(1)
        time.sleep(1)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description="Run MySQL docker")

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
        "--restart",
        help="Restart container",
        action="store_true",
    )

    args = parser.parse_args()
    db_port = int(args.db_port)
    db_name = args.db_name

    logger.info("port : %s name: %s", db_port, db_name)
    main(db_port, db_name, root_password=args.root_password, restart=args.restart)
