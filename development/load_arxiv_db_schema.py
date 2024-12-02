#!/usr/bin/python3
import os
import sys
import socket
import subprocess
import logging
import time
import shlex

logging.basicConfig(level=logging.INFO)

arxiv_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(arxiv_base_dir)

def is_port_open(host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def run_mysql_container(port: int, container_name="mysql-test", db_name="testdb"):
    """Start a mysql docker"""
    mysql_image = "mysql:5.7.20"

    subprocess.run(["docker", "pull", mysql_image], check=True)
    # subprocess.run(["docker", "kill", container_name], check=False)
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


def main() -> None:
    mysql_port = 13306
    db_name = "arxiv"
    conn_argv = [f"--port={mysql_port}", "-h", "127.0.0.1", "-u", "root", "-ptestpassword", "--ssl-mode=DISABLED"]

    if not is_port_open("127.0.0.1", mysql_port):
        run_mysql_container(mysql_port, container_name="fake-arxiv-db", db_name=db_name)

    cli = ["mysql"] + conn_argv + [db_name]
    for _ in range(20):
        if is_port_open("127.0.0.1", mysql_port):
            try:
                mysql = subprocess.Popen(cli, encoding="utf-8",
                                         stdin=subprocess.PIPE)
                mysql.communicate("select 1")
                if mysql.returncode == 0:
                    break
            except Exception as e:
                print(e)
                pass
        time.sleep(1)

    with open("arxiv_db_schema.sql") as schema_file:
        subprocess.call(cli, stdin=schema_file)

if __name__ == "__main__":
    """
    """
    main()
