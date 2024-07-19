#!/bin/sh

# File: parse_paperid_remoteaddr_from_weblogs.sh
# Goal: returns the stats day by day, split out by categories
# Desc: This script extracts paper_id:remote_addr pairs, from fastly web logs,
#       counting downloads per ip, once per hour.
#
# This script's query, is the checked in version, of what is scheduled here:
# https://console.cloud.google.com/bigquery/scheduled-queries?project=arxiv-production
#
# It runs hourly, and writes here, when it completes:
#   projects/arxiv-production/topics/papers-downloaded-by-ip-recently
# The sub:
#   https://console.cloud.google.com/cloudpubsub/subscription/detail/papers-downloaded-by-ip-recently-sub?project=arxiv-production&tab=messages
#
# You can view the current first result, from the scheduled process,like this:
# bq --project_id=arxiv-production --format=json query --nouse_legacy_sql 'SELECT * FROM arxiv_stats.papers_downloaded_by_ip_recently LIMIT 1;'
#   [{"f0_":"2024-07-18 16:00:00","paper_id":"1210.7310","remote_addr":"1.62.0.0"}]
#
# This bq results table is truncated each hour, and then loaded with the the next hours results.
# We can manually backfill by editing a time in place of the current time, and pausing the scheduled query.
#

bq --format=json query --nouse_legacy_sql --use_cache --max_rows 10 \
'
SELECT
      REGEXP_EXTRACT(STRING(json_payload.path), r"^/pdf/([a-zA-Z\.-]*/?[0-9.]+)") as paper_id,
      STRING(json_payload.remote_addr) as remote_addr,
      TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR), HOUR) as start_dttm
 FROM arxiv_logs._AllLogs
WHERE log_id = "fastly_log_ingest"
  AND left(STRING(json_payload.path), 4) = "/pdf"
  AND INT64(json_payload.status) in ( 200,206 )
  and timestamp between TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR), HOUR) and
                        TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR), HOUR)
GROUP BY 1,2,3
'
