"""Publish arxiv-base's static assets to the GCS "web static" bucket.

These are the shared assets every app should consume via
``url_for('base.static', …)`` instead of vendoring a copy — the spinout chrome
(``css/arxiv-header-footer.css``, ``js/arxiv-header.js``, the IBM Plex fonts,
the arXiv logo + funder images) plus the rest of ``arxiv/base/static``.

Buckets:
  prod : gs://arxiv-web-static       (served at https://static.arxiv.org/)
  dev  : gs://arxiv-dev-web-static   (arxiv-development)

Assets publish under ``/static/base/<BASE_VERSION>/…`` — the exact versioned
path the base blueprint serves (see ``arxiv/base/__init__.py``), so the URL
``https://<cdn>/static/base/<BASE_VERSION>/css/arxiv-header-footer.css`` resolves
1:1 with ``base.static``. Versioned paths are immutable, so **bump the package
version to roll a new release**.

Run OUT-OF-BAND (not in CI), authenticated with gcloud, once per released
BASE_VERSION. See README "Publishing static files to GCS" for one-time bucket
setup (public-read + CORS).

    python upload_static_assets.py --bucket gs://arxiv-dev-web-static   # dev
    python upload_static_assets.py --bucket gs://arxiv-web-static       # prod
"""
import os
import subprocess

import click

import arxiv.base
from arxiv.base.config import BASE_VERSION

STATIC_DIR = os.path.join(os.path.dirname(arxiv.base.__file__), "static")


@click.command()
@click.option("--bucket", required=True,
              help="gs://arxiv-web-static (prod) or gs://arxiv-dev-web-static (dev)")
@click.option("--dry-run", is_flag=True, help="show what would change; upload nothing")
def main(bucket: str, dry_run: bool) -> None:
    """rsync arxiv/base/static -> <bucket>/static/base/<BASE_VERSION>/."""
    dest = f"{bucket.rstrip('/')}/static/base/{BASE_VERSION}"
    click.echo(f"source : {STATIC_DIR}")
    click.echo(f"dest   : {dest}   (BASE_VERSION={BASE_VERSION})")
    if not dry_run and not click.confirm("Publish base static assets there?", default=True):
        click.echo("Aborted.")
        return

    rsync = ["gcloud", "storage", "rsync", "--recursive", STATIC_DIR, dest]
    if dry_run:
        rsync.append("--dry-run")
    subprocess.run(rsync, check=True)

    if not dry_run:
        # gcloud guesses Content-Type from the extension, but some versions tag
        # .woff2 as application/octet-stream, which breaks @font-face. Pin it.
        subprocess.run(
            ["gcloud", "storage", "objects", "update",
             f"{dest}/fonts/*.woff2", "--content-type=font/woff2"],
            check=False,
        )
    click.echo(f"Done. Verify: gcloud storage ls --recursive {dest}")


if __name__ == "__main__":
    main()
