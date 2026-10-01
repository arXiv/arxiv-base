# consistency-checks -- arxiv-production.
# image is passed with -var at apply time, pinned to the pushed digest.
gcp_project_id = "arxiv-production"
gcp_region     = "us-central1"

# No shared scheduler SA in arxiv-production: the scheduler starts the jobs as
# their own consistency-checks SA (scheduler_sa unset).

# Read-only DB URI secret (mysql://user:pass@host/db) on the rep12 read replica.
db_uri_secret = "arxiv-production-rep12-db-readonly_URI"
# The URI connects via unix_socket=/cloudsql/<conn> (as modapi does):
db_instance_connection_name = "arxiv-production:us-central1:arxiv-production-rep12"

data_bucket    = "arxiv-production-data"
deleted_gs_url = "gs://arxiv-production-data/deleted.json"

# Parallel run with the Perl crontab: every report goes to a test address
# until the reports have been compared. Keep every job listed: a missing key
# falls back to the check's real recipients.
mail_dry_run = false
mail_to = {
  new-accounts     = "norbert@arxiv.org"
  recent-articles  = "norbert@arxiv.org"
  db-stats         = "norbert@arxiv.org"
  deleted-papers   = "norbert@arxiv.org"
  orig-consistency = "norbert@arxiv.org"
  categories       = "norbert@arxiv.org"
}

# After the parallel run: drop the test entries above to use the checks'
# defaults (README). db-stats then needs the full nexus2.crontab list incl.
# personal addresses:
#   db-stats = "mod-admin@arxiv.org,db-stats-list@arxiv.org,je277@cornell.edu,ss3783@cornell.edu,rmr37@cornell.edu,so356@cornell.edu,jonathan@arxiv.org,jake@arxiv.org"

# Search-index counts in db_stats: create these secrets (new values; the old
# keys are in arxiv-bin git and must be rotated), then uncomment. Until then
# db_stats skips those sections.
# google_search_api_key_secret = "consistency-checks-google-search-key"
# bing_api_key_secret          = "consistency-checks-bing-key"

# FLAGS patterns for new-accounts are currently empty; once there are some, put
# them in a secret and set:
# flags_secret = "consistency-checks-flags"
