#!/bin/bash
#
PASSWORD=$(< ~/.arxiv/arxvi-db-read-only-password)
mysqldump -h 127.0.0.1 --port 2021 -u readonly -p"$PASSWORD" --no-data --set-gtid-purged=OFF --skip-comments  arXiv |  sed 's/ AUTO_INCREMENT=[0-9]*\b/ AUTO_INCREMENT=1/' > arxiv/db/arxiv_db_schema.sql
