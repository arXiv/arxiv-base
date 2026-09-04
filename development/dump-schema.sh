#!/bin/bash


PASSWORD=$(gcloud secrets versions access latest --project=arxiv-production  --secret=arxiv-production-rep11-db-readonly)

USE_DOCKER=0
if command -v mysqldump &>/dev/null
then
  # mysqldump is here, but could be mariadump which does NOT WORK!
  if mysqldump --version 2>&1 | grep -qi mariadb ; then
    USE_DOCKER=1
  fi
else
  USE_DOCKER=1
fi

DOCKER=""
if [ $USE_DOCKER = 1 ] ; then
  DOCKER="docker run --net=host -ti mysql:8.4.5 "
fi
$DOCKER mysqldump -h 127.0.0.1 --port 2021 -u readonly -p"$PASSWORD" --no-data --set-gtid-purged=OFF --skip-comments  arXiv |  sed 's/ AUTO_INCREMENT=[0-9]*\b/ AUTO_INCREMENT=1/' > arxiv/db/arxiv_db_schema.sql


echo "CHECK FOR LINE ENDINGS, MIGHT BE DOS!!"
echo "CHECK FOR PASSWORD WARNING ON TOP OF arxiv/db/arxiv_db_schema.sql"

