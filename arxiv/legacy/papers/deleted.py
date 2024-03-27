"""Papers that are deleted or never existed."""

from typing import Optional, Literal
import re
import os
import json

from google.cloud import storage

DEFAULT_DELETED_GS_URL = "gs://arxiv-production-data/deleted.json"

_verregex = re.compile(r'v\d+$')

_deleted_data = None

def ensure_deleted_data(location: Optional[str] = None) -> None:
    """Checks that deleted data loads from Google storage and is not empty.

    Raises an Exception if there are problems.
    """
    rd = get_deleted_data(location)
    if not rd:
        raise Exception("Deleted data was empty")


def get_deleted_data(location: Optional[str] = None)->dict:
    """Get the deleted data.

    `get_deleted_data()` will attempt to get the data from GS only
    once. If it fails it will cache a "LOAD FAILED" result that will
    cause it to fail when called further in the execution. This is to
    avoid repeted API calls to the GS bucket.

    `location` should be a GS bucket in the form
    gs://bucketname/some/key/data.json. If location is not
    provided the env var DELETED_GS_URL will be used and if that
    doesn't exist a default value for the URL will be used.

    This will load from GS once and save in a package level variable.

    If `deleted()` is to be used in an app it makes sense to call
    `get_deleted_data()` when starting that app to ensure the app has
    access and it is configured correctly.
    """
    global _deleted_data
    if _deleted_data is not None:
        return _deleted_data
    if _deleted_data == "LOAD FAILED":
        raise Exception("Previous load of deleted data failed, not trying again "
                        "until _deleted_data is cleared by setting it to None")

    if location is None:
        location = os.environ.get("DELETED_GS_URL", DEFAULT_DELETED_GS_URL)

    blob = None
    try:
        bucket_name = location.strip('gs://').split('/')[0]
        key = '/'.join(location.strip('gs://').split('/')[1:])
        bucket = storage.Client().bucket(bucket_name)
        blob = bucket.get_blob(key)
    except Exception as ex:
        _deleted_data = "LOAD FAILED"
        raise ex

    if not blob:
        _deleted_data = "LOAD FAILED"
        raise Exception(f"Could not get resons file from {location}")

    try:
        with blob.open('r') as fp:
            _deleted_data = json.load(fp)
            return _deleted_data
    except Exception as ex:
        _deleted_data = "LOAD FAILED"
        raise ex


def is_deleted(id: str) -> Optional[str]:
    """Checks if an id is for a deleted paper.

    Expects a ID without a version such as quant-ph/0411165 or 0901.4014
    or 1203.23434.
    """
    if not id:
        return None
    else:
        return get_deleted_data().get(id, None)
