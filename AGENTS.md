# Agent Instructions

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`arxiv-base` is the shared dependency hub for arXiv services (browse, search, submit-ce, feed,
auth, fulltext, …). Changes here are cross-cutting: a change to `arxiv.base`, `arxiv.db`,
`arxiv.auth`, `arxiv.taxonomy`, or the static assets propagates to every consumer. Verify against
the dependent repo(s) the task cares about.

It is also **four independently-managed Python packages in one git repo**, each with its own
toolchain and its own CI workflow. Check which one you are in before running anything:

| Path | Package | Tooling | Python | CI |
| --- | --- | --- | --- | --- |
| `/` (`arxiv/`, `fourohfour/`, `tests/`) | `arxiv-base` | poetry | ^3.11 | `.github/workflows/pullrequest_tests.yaml` |
| `qa/` | `qa` | uv + ruff + ty | >=3.11,<3.14 | `qa-triggers.yml` → `lint-test-package.yml` |
| `arxiv-functions/` | `arxiv-functions` | uv + ruff + ty | ~=3.13 | `arxiv-functions-triggers.yml` → `lint-test-package.yml` |
| `gcp/service_auth/` | `gcp-service-auth` | poetry | — | (none) |

`qa/` depends on `arxiv-base` from git, not from the working tree — `pyproject.toml` pins
`branch = "master"` and stubs out its transitive deps. A root-package change is not automatically
visible to `qa/`.

## Commands

### Root package (poetry)

```bash
poetry install --with=dev                 # base install
poetry install --with=dev --extras qa     # adds gcld3; needs protobuf-compiler installed
poetry check --lock                       # CI fails if poetry.lock is stale vs pyproject.toml

FLASK_APP=app.py FLASK_DEBUG=1 poetry run flask run   # dev server → http://127.0.0.1:5000/styleguide

poetry run pytest tests                                        # top-level tests
poetry run pytest arxiv                                        # package tests (live beside the code)
poetry run pytest arxiv/base/tests/test_urls_config.py         # one file
poetry run pytest arxiv/base/tests/test_static_urls.py -k static_url_path   # one test
poetry run python tests/run_app_tests.py                       # app-config compliance tests
```

Two pytest specifics defined in `pytest.ini` / root `conftest.py`:

- `--db=sqlite|mysql` (default `sqlite`) selects the backend for DB-backed tests. `--db=mysql`
  runs `development/load_arxiv_db_schema.py`, which starts a MySQL docker container on port
  25336 and loads `arxiv/db/arxiv_db_schema.sql`. The `classic_db_engine` fixture **aborts** if
  the target DB has >20 populated tables or an `arXiv_metadata` table — a guard against pointing
  tests at a real database.
- The `with_op` marker (tests needing the 1Password CLI) is excluded by default via `addopts`.

CI coverage gates (`pullrequest_tests.yaml`) — match these locally before pushing:

```bash
poetry run pytest --cov=arxiv.base --cov=arxiv.metadata --cov-fail-under=85 arxiv
poetry run pytest --cov=fourohfour --cov-fail-under=74 fourohfour --cov-append
poetry run pytest --cov=arxiv --cov-fail-under=82 arxiv --cov-append
poetry run pytest --cov=arxiv --cov-fail-under=40 arxiv --ignore=arxiv/base --ignore=arxiv/auth/legacy --db=sqlite --cov-append
cd arxiv && poetry run pytest auth/legacy/tests --db=mysql    # legacy auth against real MySQL
```

`make test` runs a similar set through a `venv/`-installed poetry, and expects a MySQL on
port 13306 (see `tests/docker-compose.yml`). `mypy.ini`, `.pylintrc`, and `nose2.cfg` exist but
no type or lint check runs in CI for the root package — the mypy step is commented out with
"types are in bad shape".

### `qa/` and `arxiv-functions/` (uv)

```bash
cd qa && make lint && make type && make format && make test    # ruff, ty, ruff format, pytest ≥80%
cd arxiv-functions && uv sync --dev
uv run ruff check . && uv run ruff format --check && uv run ty check
uv run pytest tests/ --cov=arxiv_functions --cov-fail-under=80 --confcutdir=tests
```

`--confcutdir=tests` matters: without it, pytest walks up and picks up the root `conftest.py`,
which imports Flask and the DB layer.

### Assets and generated code

```bash
sass arxiv/base/static/sass/arxivstyle.sass:arxiv/base/static/css/arxivstyle.css   # --watch to autocompile
make db-codegen                                       # regenerate arxiv/db/models.py
python upload_static_assets.py --bucket gs://arxiv-dev-web-static --dry-run
```

## Architecture

### `arxiv.base.Base` — the Flask extension

`arxiv/base/__init__.py` is the entry point every consuming app calls (`Base(app)`). Beyond
registering the base blueprint (templates + static), it does invasive things that are
deliberate and fragile — do not "clean them up":

- Rewrites `app.static_url_path` to `/static/<app.name>/<APP_VERSION>` by removing the existing
  rule from `app.url_map._rules`, clearing `_rules_by_endpoint['static']`, deleting
  `view_functions['static']`, and re-adding the rule.
- Monkeypatches `app.register_blueprint` (saving the original as `app._register_blueprint`) so
  every later-registered blueprint gets a static path under the app-versioned prefix.
- Serves base's own assets from `/static/base/<BASE_VERSION>`, so apps on different base
  versions never clobber each other's cached assets.
- Registers exception handlers, template filters, context processors, the `arxiv:` URL
  converter, and a `teardown_appcontext` hook calling `arxiv.db.Session.remove()`.

`arxiv/base/routes.py` and `arxiv/base/factory.py` are **dev/test only** — the `/styleguide`
blueprint is not attached by `Base`.

`arxiv.base.app_tests` is an importable `unittest` suite that downstream apps run against their
own factory to check config/static-path compliance; `tests/run_app_tests.py` is base's own
invocation of it.

### Two config systems

- `arxiv/config/__init__.py` — pydantic-settings `Settings`, read from env. This is what
  `arxiv.db` and non-Flask consumers use.
- `arxiv/base/config.py` — module-level constants read from `os.environ`, loaded into
  `app.config` via `from_object`.

Both define `BASE_SERVER`/`AUTH_SERVER`/`SEARCH_SERVER`/`SUBMIT_SERVER`/`HELP_SERVER` and the
`URLS` table of external endpoints. **Adding or changing an external URL generally means editing
both.** `arxiv/base/urls/` installs the `url_for()` `BuildError` fallback that resolves those
endpoints to absolute cross-service URLs.

### `arxiv.db` — engine configured at import time

`configure_db(settings)` runs at module load, so importing `arxiv.db` already creates an engine
from the environment. To point at a different DB after import, call `arxiv.db.init(settings)`
(which also re-binds `arxiv.db.models`), or `configure_db_engine(engine, latexml_engine)` as the
test fixtures do.

`Session` is a `scoped_session` whose scope function returns the Flask **app context** id when
one is active and the thread id otherwise — so `Session.execute(...)` works directly in Flask,
while non-Flask code should use `with Session() as session:`. `transaction()` is the
commit-on-success context manager; it does not close the session inside Flask (teardown does).

### `arxiv/db/models.py` is generated — do not edit it

Pipeline documented in `development/README.md`:

```
MySQL schema (arxiv/db/arxiv_db_schema.sql) + arxiv/db/arxiv-db-metadata.yaml
    → patched sqlacodegen (development/sqlacodegen/) → arxiv/db/autogen_models.py
arxiv/db/models.py-orig + autogen_models.py → LibCST merge → arxiv/db/models.py
```

To change a model, edit **`arxiv/db/models.py-orig`** (hand-maintained portion) or
`arxiv/db/arxiv-db-metadata.yaml` (class/table name overrides, column and relationship
overrides), then run `make db-codegen`. A **new table does not appear automatically** — copy the
generated class from `autogen_models.py` into `models.py-orig` and re-run.
`arxiv/db/tests/test_db_schema.py` imports every model by name and exercises the generated
schema, so a model that fails to make it through the merge shows up there;
`test_schema_checker.py` covers the LibCST merge machinery itself.

### `arxiv.auth`

Two coexisting mechanisms, both installed by `Auth(app)` which sets `request.auth` to an
`arxiv.auth.domain.Session`:

- `arxiv/auth/legacy/` — classic Tapir tables (`TapirUser`, `TapirNickname`,
  `TapirUsersPassword`, `TapirSession`, `TapirPermanentToken`), cookie handling, endorsements.
  DB-backed, so its tests are the ones that need MySQL.
- `arxiv/auth/auth/` — NG JWT tokens, scopes, decorators, and a stateless cookie/JWT
  `SessionStore` (Redis was removed). `AuthMiddleware` exists but is not used in production.

`arxiv/auth/openid/`, `user_claims.py`, and `user_claims_to_legacy.py` bridge OIDC claims onto
legacy user records.

### Static assets and shared site chrome

`arxiv/base/static/` is the **single source of truth** for the shared header/footer/announcement
chrome and fonts; every app consumes it rather than vendoring a copy. Assets are published
out-of-band (not CI) to GCS at the immutable path `/static/base/<BASE_VERSION>/…`, so
**releasing a chrome change means bumping the package version** in `pyproject.toml`. See the
"Publishing static files to GCS" section of `README.md`.

Two files that must not be hand-edited:

- `static/css/arxivstyle.css` — compiled from `static/sass/arxivstyle.sass` (Bulma with arXiv
  overrides; Bulma sources are vendored in `static/sass/` so variables can be overridden).
- The `.ds-*` component rules in `static/css/arxiv-header-footer.css` — a re-syncable subset
  extracted from the design system. `docs/shared-chrome.md` explains the provenance and the two
  specificity hacks that exist to beat legacy host stylesheets; read it before touching that file.

### Other significant modules

- `arxiv/taxonomy/definitions.py` — hand-maintained `GROUPS`/`ARCHIVES`/`CATEGORIES` dicts,
  the canonical arXiv taxonomy for all services, including aliases and end-dated archives.
  `category.py` holds the `Group`/`Archive`/`Category` types.
- `arxiv/metadata/` (`metacheck.py`) and `qa/qa/checks/` — two generations of metadata quality
  checking. `qa/` is the newer registry: importing the package populates `checks:
  list[BaseCheck]`, and per its README you must **bump a check's `version` whenever its logic or
  `on_failure_policy` changes**.
- `arxiv/base/urls/links.py` — the combined arXiv-id / DOI / URL detection-and-linkification
  used in abstract rendering. Deliberately one pass over the text, not several jinja filters.
- `arxiv/files/` — `object_store.py` abstraction over GCS/local, `key_patterns.py` for canonical
  object keys, `fileformat.py`.
- `fourohfour/` — standalone 404 app with its own Pipfile and its own CI coverage gate.
- `arxiv/ops/`, `arxiv/formats/`, `arxiv/files/` are excluded from coverage (`.coveragerc`).

## Gotchas

- The root `Dockerfile` is stale (CentOS 7, Python 3.6, pipenv) and is not the deployment path.
- `README.md`'s pypi section references `setup.py`, which no longer exists — the build backend is
  poetry-core.
- `.github/workflows/pullrequest_tests.yaml` ignores `qa/**` and `arxiv-functions/**`; those have
  their own triggers. A root-package change plus a `qa/` change runs two independent pipelines.
