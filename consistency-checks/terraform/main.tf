# consistency-checks: one Cloud Run Job per check, each started by a Cloud Scheduler
# job. All jobs run the same image (consistency-checks/Dockerfile) with different args.
#
#   terraform init -backend-config="bucket=<tf state bucket>"
#   terraform apply -var-file=envs/<env>.tfvars -var="image=<registry>/consistency-checks@sha256:..."

terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "consistency-checks"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

locals {
  # Schedules follow arxiv-bin dotfiles/nexus2.crontab (America/New_York).
  jobs = {
    new-accounts = {
      # Perl ran Mon-Fri with a 24h window and so never looked at weekend
      # sign-ups; daily closes that gap.
      args     = ["new_accounts"]
      schedule = "30 8 * * *"
      timeout  = "600s"
      cpu      = "1"
      memory   = "512Mi"
      flags    = true
    }
    recent-articles = {
      args     = ["recent_articles", "--days", "1"]
      schedule = "20 12,16 * * 1-5"
      timeout  = "3600s"
      cpu      = "2"
      memory   = "2Gi"
      flags    = false
    }
    db-stats = {
      args     = ["db_stats"]
      schedule = "29 6 * * 1"
      timeout  = "1800s"
      cpu      = "1"
      memory   = "1Gi"
      flags    = false
    }
    deleted-papers = {
      args     = ["deleted_papers"]
      schedule = "33 5 * * 6"
      timeout  = "900s"
      cpu      = "1"
      memory   = "512Mi"
      flags    = false
    }
    orig-consistency = {
      args     = ["orig_consistency"]
      schedule = "33 3 * * 6"
      timeout  = "21600s"
      cpu      = "2"
      memory   = "4Gi"
      flags    = false
    }
    categories = {
      # full scan reads every current .abs (~3M objects); Perl crosses.pl took ~3h
      args     = ["categories"]
      schedule = "30 5 * * 1"
      timeout  = "43200s"
      cpu      = "2"
      memory   = "4Gi"
      flags    = false
    }
  }

  secret_env = merge(
    {
      DB_URL   = var.db_uri_secret
      SMTP_URI = var.smtp_uri_secret
    },
    var.google_search_api_key_secret == "" ? {} : { GOOGLE_SEARCH_API_KEY = var.google_search_api_key_secret },
    var.bing_api_key_secret == "" ? {} : { BING_API_KEY = var.bing_api_key_secret },
  )
  secrets = distinct(compact(concat(values(local.secret_env), [var.flags_secret])))

  plain_env = {
    GOOGLE_CLOUD_PROJECT = var.gcp_project_id
    BUCKET               = var.data_bucket
    DELETED_GS_URL       = var.deleted_gs_url
    MAIL_DRY_RUN         = tostring(var.mail_dry_run)
    MAIL_FROM            = var.mail_from
    WORKERS              = tostring(var.workers)
  }
}

# ---------------------------------------------------------------------------
# Service account + IAM (read-only on DB and data)
# ---------------------------------------------------------------------------

resource "google_service_account" "checks" {
  account_id   = "consistency-checks"
  display_name = "consistency-checks Cloud Run Jobs (read-only DB and data checks)"
}

resource "google_project_iam_member" "checks" {
  for_each = toset(["roles/logging.logWriter", "roles/cloudsql.client"])
  project  = var.gcp_project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.checks.email}"
}

resource "google_storage_bucket_iam_member" "data_reader" {
  bucket = var.data_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.checks.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = toset(local.secrets)
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.checks.email}"
}

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

resource "google_cloud_run_v2_job" "check" {
  for_each = local.jobs
  name     = "consistency-checks-${each.key}"
  location = var.gcp_region

  template {
    template {
      service_account = google_service_account.checks.email
      # a failed check reruns next schedule; retrying would only double-mail
      max_retries = 0
      timeout     = each.value.timeout

      # only needed when the DB URI connects via unix_socket=/cloudsql/<conn>
      dynamic "volumes" {
        for_each = var.db_instance_connection_name == "" ? [] : [1]
        content {
          name = "cloudsql"
          cloud_sql_instance {
            instances = [var.db_instance_connection_name]
          }
        }
      }
      dynamic "volumes" {
        for_each = each.value.flags && var.flags_secret != "" ? [1] : []
        content {
          name = "flags"
          secret {
            secret = var.flags_secret
            items {
              version = "latest"
              path    = "FLAGS"
            }
          }
        }
      }

      containers {
        image = var.image
        args  = concat(each.value.args, lookup(var.mail_to, each.key, "") == "" ? [] : ["--mail-to", var.mail_to[each.key]])

        resources {
          limits = {
            cpu    = each.value.cpu
            memory = each.value.memory
          }
        }

        dynamic "env" {
          for_each = local.plain_env
          content {
            name  = env.key
            value = env.value
          }
        }
        dynamic "env" {
          for_each = local.secret_env
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }

        dynamic "volume_mounts" {
          for_each = var.db_instance_connection_name == "" ? [] : [1]
          content {
            name       = "cloudsql"
            mount_path = "/cloudsql"
          }
        }
        dynamic "volume_mounts" {
          for_each = each.value.flags && var.flags_secret != "" ? [1] : []
          content {
            name       = "flags"
            mount_path = "/secrets/flags"
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.secret_access]
}

# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  for_each = local.jobs
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_job.check[each.key].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.scheduler_sa}"
}

resource "google_cloud_scheduler_job" "check" {
  for_each    = local.jobs
  name        = "consistency-checks-${each.key}"
  description = "Runs Cloud Run Job consistency-checks-${each.key}"
  schedule    = each.value.schedule
  time_zone   = "America/New_York"
  region      = var.gcp_region
  paused      = var.schedules_paused

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.gcp_project_id}/locations/${var.gcp_region}/jobs/${google_cloud_run_v2_job.check[each.key].name}:run"
    oauth_token {
      service_account_email = var.scheduler_sa
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}

# ---------------------------------------------------------------------------
# Alert when a check itself fails (findings exit 0, only crashes exit non-zero)
# ---------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "check_failed" {
  count        = length(var.notification_channels) > 0 ? 1 : 0
  display_name = "consistency-checks job execution failed"
  combiner     = "OR"
  conditions {
    display_name = "failed consistency-checks execution"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_job\" AND resource.labels.job_name = starts_with(\"consistency-checks-\") AND metric.type = \"run.googleapis.com/job/completed_execution_count\" AND metric.labels.result = \"failed\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
  notification_channels = var.notification_channels
  documentation {
    content = "An consistency-checks Cloud Run Job execution failed (the check crashed, not a finding). See the execution logs of the job named in the incident."
  }
}
