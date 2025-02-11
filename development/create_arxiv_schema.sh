#!/bin/bash

DB_NAME="arXiv"
DB_USER="testuser"
DB_PASSWORD="testpassword"
CHARSET="utf8mb4"
COLLATION="utf8mb4_unicode_ci"

sudo mysql  <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET ${CHARSET} COLLATE ${COLLATION};
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

# echo "Database '${DB_NAME}' and user '${DB_USER}' setup completed successfully."

mysql -h 127.0.0.1 --user $DB_USER -p$DB_PASSWORD  $DB_NAME < ../arxiv/db/arxiv_db_schema.sql
