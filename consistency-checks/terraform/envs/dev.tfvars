# consistency-checks -- arxiv-development.
# image is passed with -var at apply time, pinned to the pushed digest.
gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"

scheduler_sa = "cloud-scheduler@arxiv-development.iam.gserviceaccount.com"

# Read-only DB URI secret (mysql://user:pass@host/db) on the dev-db-6 read replica.
db_uri_secret = "dev-db-6-readonly-uri"
# Only if that URI connects via unix_socket=/cloudsql/<conn>:
# db_instance_connection_name = "arxiv-development:us-central1:dev-db-6"

data_bucket = "arxiv-dev-data"
# Copy of gs://arxiv-production-data/deleted.json (made 2026-09-24; the job SA
# only reads data_bucket). Re-copy when the prod list changes.
deleted_gs_url = "gs://arxiv-dev-data/deleted.json"

mail_dry_run = true

# dev-db-6 replicates the full DB while arxiv-dev-data may hold only part of the
# files, so scheduled full scans would mostly report missing files. Keep the
# schedules paused and run jobs on demand:
#   gcloud run jobs execute consistency-checks-<name> --region us-central1 --project arxiv-development
schedules_paused = true

# No search-index API keys in dev: db_stats skips those sections.

# FLAGS patterns for new-accounts are currently empty; once there are some, put
# them in a secret and set:
# flags_secret = "consistency-checks-flags"
