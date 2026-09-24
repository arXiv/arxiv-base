variable "gcp_project_id" {
  type = string
}

variable "gcp_region" {
  type    = string
  default = "us-central1"
}

variable "image" {
  type        = string
  description = "consistency-checks image (consistency-checks/Dockerfile), preferably pinned by digest."
}

# --- DB -----------------------------------------------------------------------

variable "db_uri_secret" {
  type        = string
  description = "Name of the Secret Manager secret holding the READ-ONLY DB URI (mysql://user:pass@host/db); injected as DB_URL."
}

variable "db_instance_connection_name" {
  type        = string
  default     = ""
  description = "Cloud SQL instance (project:region:instance) to mount at /cloudsql. Only needed if the DB URI uses unix_socket=/cloudsql/<conn>."
}

# --- Data ---------------------------------------------------------------------

variable "data_bucket" {
  type        = string
  default     = "arxiv-production-data"
  description = "Bucket with abs/, ftp/, orig/, ps_cache/, txt/."
}

variable "deleted_gs_url" {
  type    = string
  default = "gs://arxiv-production-data/deleted.json"
}

# --- Mail ---------------------------------------------------------------------

variable "smtp_uri_secret" {
  type        = string
  default     = "HALON_CREDS"
  description = "Secret holding smtps://user:password@host:port (same secret as arxiv-mail-sender)."
}

variable "mail_dry_run" {
  type        = bool
  default     = true
  description = "Log reports instead of mailing them. Set false once the reports look right."
}

variable "mail_from" {
  type    = string
  default = "cloudcron@arxiv.org"
}

variable "mail_to" {
  type        = map(string)
  default     = {}
  description = "Per-job recipient override (key = job key, e.g. db-stats), comma separated. Default is each check's own (see README)."
}

# --- Other secrets ------------------------------------------------------------

variable "flags_secret" {
  type        = string
  default     = ""
  description = "Secret holding the FLAGS patterns file (arxiv-bin report/FLAGS) for new-accounts; empty = no patterns (the FLAGS file is currently empty)."
}

variable "google_search_api_key_secret" {
  type        = string
  default     = ""
  description = "Secret with the Google Custom Search API key for db-stats index counts; empty skips them."
}

variable "bing_api_key_secret" {
  type        = string
  default     = ""
  description = "Secret with the Bing Webmaster API key for db-stats index counts; empty skips them."
}

# --- Scheduling / ops ---------------------------------------------------------

variable "scheduler_sa" {
  type        = string
  description = "Service account Cloud Scheduler uses to start the jobs (gets run.invoker on each)."
}

variable "schedules_paused" {
  type    = bool
  default = false
}

variable "workers" {
  type        = number
  default     = 32
  description = "Parallel bucket reads per job."
}

variable "notification_channels" {
  type        = list(string)
  default     = []
  description = "Monitoring channels alerted when a check execution fails; empty creates no alert."
}
