"""Use this to upload static content to S3."""

import click
import flask_s3
from arxiv.base.factory import create_web_app

app = create_web_app()
with app.app_context():
    sup = app.static_url_path
    if click.confirm(f'Upload static assets for {sup} to public S3 bucket at {app.config.get("FLASKS3_BUCKET_NAME")}?', default=True):
        flask_s3.create_all(app)
    else:
        print("Aborted.")
