# consistency-checks

Scheduled consistency checks on the classic DB and the data bucket
(`abs/`, `ftp/`, `orig/`, `ps_cache/`, `txt/`). Replaces the e-prints Perl
cron checks from `arxiv-bin` / `arxiv-analysis`.

One image, one Cloud Run Job per check, each started by Cloud Scheduler:

```
python -m consistency_checks <check> [--mail-to ADDR] [--no-mail] [-v] [check options]
```

A check prints its report. It mails the report when it found problems. The
periodic `db_stats` report is mailed every time, and `-v` forces a mail. The
exit status is non-zero only when the check itself failed. A failed Cloud Run
execution therefore means "the check is broken", not "the check found
something".

## Checks

| Check | Replaces | What it does | Schedule (ET) | Mails to |
|---|---|---|---|---|
| `new_accounts` | `cron/watch_new_accounts.pl` | New accounts (default: last 24 h) matched against the FLAGS patterns | daily 08:30 | system-queue@ |
| `recent_articles` | `cron/check_recently_updated_articles.pl` | Files written in the last day: `.tar.gz` lists, `.gz` decompresses, `pdfinfo` clean, `.abs` parses with canonical categories and a valid license | Mon–Fri 12:20, 16:20 | sheriff@ |
| `db_stats` | `cron/db_stats.pl` | User/article stats, moderation gaps, Google/Bing index counts | Mon 06:29 | mod-admin@, db-stats-list@ |
| `deleted_papers` | `test/check_deleted_papers.pl` | Deleted papers: zero-size abs, source kept, no DB rows | Sat 05:33 | cron-errors@ |
| `orig_consistency` | `cron/check_files_in_orig.pl` + `test/check_abs_src_files.pl` | ftp/ holds the abs + source of each current version, orig/ of each older version; nothing else in there | Sat 03:33 | sheriff@ |
| `categories` | `crosses.pl -C` + `test/check_categories.pl -a` | Categories are valid and canonical, and agree between abs, `arXiv_in_category` and `arXiv_metadata.abs_categories` | Mon 05:30 | cron-errors@ |

Schedules and recipients follow `arxiv-bin/dotfiles/nexus2.crontab`. For two
merged checks, the earlier or Monday slot was kept. Differences:
`new_accounts` runs daily (see below). The crontab also mailed `db_stats` to
six personal addresses; they are in `envs/prod.tfvars` as a commented `mail_to`
entry, ready to activate. `crosses.pl` output was mailed on every run, while
`categories` mails only when it finds something.

`orig_consistency` and `categories` take `--yymm 2101,2103-2105` to limit a run.

### Changes from the Perl scripts

- `recent_articles` finds recent papers from `arXiv_metadata` (`created`/`updated`
  in the window). It then keeps only the bucket objects written in the window.
  A bucket has no ctime, and listing it all to filter by date would be slow.
- `orig_consistency` compares the bucket with the DB: every version must have
  its files, and no files may exist without a version. The Perl script only
  counted files per version. Withdrawn versions only need their abs.
- The ownership and mode checks (`check_abs_src_files.pl`) and all
  DB-writing fix modes (`crosses.pl -F -s -A -X`) were dropped.
- The `check_versions` history check in `check_files_in_orig.pl` only ran for
  the on-prem "not yet rolled in" (unversioned) files in orig. It was not
  ported. Such files are now reported as unexpected.
- `new_accounts` runs daily. Perl ran Mon–Fri with a 24 h window and so never
  looked at weekend sign-ups.
- The deleted-papers list comes from `deleted.json` (`arxiv.legacy.papers.deleted`),
  not the Perl hash.
- The historical category exceptions (known bad primaries, funct-an → math.OA)
  were generated from `arxiv-lib` into `consistency_checks/legacy_categories.py`.

### Not ported

- `cron/get_unhandled_submissions.pl`: left out for now. The crontab runs it Mon–Fri at 08:00 (`-m -o`) and 17:00 (`-m -n -s`).
- **OPEN DISCUSSION: `arxiv-analysis/author_id_stats.pl`.** In the crontab it
  runs Mondays at 08:15 (`-g`) and 08:17 (`-w`), mailing the weekly counts and
  an EPS graph to busybody@arxiv.org. Its web-log part (`/a/<id>` hits in CIT
  access logs) and the gnuplot graph are obsolete in GCP. Still to decide: port the author-ID/ORCID
  creation counts (by month/week/day, from `arXiv_author_ids` and
  `arXiv_orcid_ids`), perhaps as a section of `db_stats`, or drop it.
- TODO: the Perl checks also looked for cross-list placeholder files
  (`ftp/<archive>/papers/<yymm>/<other-archive><num>.abs`). None were found in
  `gs://arxiv-production-data` (sampled 2026-09). Re-add the check if a full
  scan ever finds any.

## Configuration

Settings are read from environment variables (and `.env`).

| Variable | Purpose |
|---|---|
| `DB_URL` | DB URI, e.g. `mysql://user:pass@host/arXiv`. In Cloud Run it is injected from the read-only DB URI secret (Terraform `db_uri_secret`, prod: `arxiv-production-rep12-db-readonly_URI`). |
| `BUCKET` / `LOCAL_DATA_DIR` | data bucket (default `arxiv-production-data`), or a local directory with the same layout |
| `DELETED_GS_URL` | location of `deleted.json` |
| `MAIL_DRY_RUN` | default `true`: log instead of sending |
| `SMTP_URI` | `smtps://user:password@host:port` (or `smtp+starttls://`). Same secret as arxiv-mail-sender (`HALON_CREDS`). |
| `MAIL_FROM` | default `cloudcron@arxiv.org` |
| `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_CX`, `BING_API_KEY`, `SEARCH_INDEX_HOSTS` | `db_stats` index counts. A missing key skips that section. |
| `WORKERS` | parallel bucket reads (default 32) |

`new_accounts --flags-file` defaults to `/secrets/flags/FLAGS`, mounted from
the Terraform `flags_secret` if set. A missing file means no patterns. Its format: `# comment` lines set the
note for the patterns that follow, and a pattern line is one or more regexes
joined by ` && `, all of which must match.

## Development

```bash
cd consistency-checks
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check && uv run ty check

# run a check locally against a DB and a local copy of the bucket layout
DB_URL=mysql+mysqldb://user:pw@host/arXiv LOCAL_DATA_DIR=/data uv run python -m consistency_checks recent_articles --no-mail
```

## Build and deploy

With the Makefile in this directory (`ENV=dev` for arxiv-development, the
default, or `ENV=prod` for arxiv-production):

```bash
make docker-auth            # once: docker login for Artifact Registry
make build                  # local image consistency-checks:<git describe --dirty>
make deploy ENV=dev         # build, push, terraform plan pinned to the pushed digest
make apply  ENV=dev         # apply exactly the reviewed plan (terraform/tfplan-dev)
```

`make push` and `make plan` also work on their own. `IMAGE=...` deploys some
other image, and `TAG=...` overrides the default tag (`git describe --always --dirty`). Images go to
`us-central1-docker.pkg.dev/<project>/{arxiv-dev-docker|arxiv-docker}/consistency-checks`.
Terraform state is kept in `{dev|prod}-arxiv-terraform-state` under the prefix
`consistency-checks`. `cloudbuild.yaml` builds the same image in Cloud Build instead.

In arxiv-development the schedules are paused; run jobs on demand with `gcloud run jobs execute`.

Before the first apply:

1. Check how the URI in `db_uri_secret` reaches the replica. A
   `unix_socket=/cloudsql/...` URI needs `db_instance_connection_name` set. A
   private-IP host needs VPC egress on the jobs, which is not configured yet.
2. FLAGS patterns: the file is currently empty, so no secret is needed. Once it
   has patterns, store it as a secret and set `flags_secret`.
3. **Rotate** the Slack webhook, Google API key and Bing API key that are
   committed in `arxiv-bin` (`get_unhandled_submissions.pl`, `db_stats.pl`).
   Store the new Google and Bing keys as `consistency-checks-google-search-key` and
   `consistency-checks-bing-key`.

### Rollout

1. Apply with `mail_dry_run = true`. The reports appear in each job's
   execution logs.
2. Run next to the Perl crontab for about two weeks and compare the reports.
   Then set `mail_dry_run = false`, at first with `mail_to` pointing at a test
   address.
3. Switch the recipients to the defaults (see the table above) and remove
   the Perl crontab entries.

Expected runtimes: `categories` reads every current abs (~3M objects).
Measured from outside GCP, that is about 10 ms per abs with 32 workers, so a
few hours per full run, similar to `crosses.pl`'s 3 h. Inside GCP it should be
faster. The job timeouts (6 h `orig_consistency`, 12 h `categories`) leave
headroom.
