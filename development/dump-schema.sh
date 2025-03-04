#!/bin/bash
#
PASSWORD=$(< ~/.arxiv/arxvi-db-read-only-password)
mysqldump -h 127.0.0.1 --port 2021 -u readonly -p"$PASSWORD" --no-data arXiv > arxiv_db_schema.sql
