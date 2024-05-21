#!/bin/sh
/cloudsql/cloud-sql-proxy arxiv-development:us-central1:latexml-db -u /cloudsql &
/cloudsql/cloud-sql-proxy arxiv-development:us-east4:arxiv-db-dev -u /cloudsql &

gunicorn --bind 0.0.0.0:8000 -t 600 -w 12 --threads 2 entry_point:app
