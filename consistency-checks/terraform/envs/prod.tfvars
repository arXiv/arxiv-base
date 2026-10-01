# consistency-checks -- arxiv-production.
# image is passed with -var at apply time, pinned to the pushed digest.
gcp_project_id = "arxiv-production"
gcp_region     = "us-central1"

scheduler_sa = "cloud-scheduler@arxiv-production.iam.gserviceaccount.com"

# Read-only DB URI secret (mysql://user:pass@host/db) on the rep12 read replica.
db_uri_secret = "arxiv-production-rep12-db-readonly_URI"
# Only if that URI connects via unix_socket=/cloudsql/<conn>:
# db_instance_connection_name = "arxiv-production:us-central1:arxiv-production-rep12"

data_bucket    = "arxiv-production-data"
deleted_gs_url = "gs://arxiv-production-data/deleted.json"

# Parallel run with the Perl crontab: keep dry-run until reports have been
# compared, then set false (and send the first weeks to a test address via mail_to).
mail_dry_run = true

# Per-job recipient overrides (replace the check's default). db-stats: the full
# nexus2.crontab list incl. personal addresses; uncomment to activate.
# mail_to = {
#   db-stats = "mod-admin@arxiv.org,db-stats-list@arxiv.org,je277@cornell.edu,ss3783@cornell.edu,rmr37@cornell.edu,so356@cornell.edu,jonathan@arxiv.org,jake@arxiv.org"
# }

# Create these secrets before applying (new values; the old keys are in git and must be rotated):
google_search_api_key_secret = "consistency-checks-google-search-key"
bing_api_key_secret          = "consistency-checks-bing-key"

# FLAGS patterns for new-accounts are currently empty; once there are some, put
# them in a secret and set:
# flags_secret = "consistency-checks-flags"
