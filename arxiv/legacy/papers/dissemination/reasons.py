"""Reasons that some papers cannot produce formats.

The function `get_reasons_data()` in this package depends on access to
`DEFAULT_REASONS_GS_URL` in google storage.
"""

from typing import Optional, Literal
import re
import os
import json

from google.cloud import storage

FORMATS = Literal['ps', 'pdf', 'html', 'dvi', 'postscript']

DEFAULT_REASONS_GS_URL = "gs://arxiv-production-data/reasons.json"

_verregex = re.compile(r'v\d+$')

_reasons_data = None

def ensure_reasons_data(location:Optional[str]=None) -> None:
    """Checks that reasons data loads from Google storage and is not empty.

    Raises an Exception if there are problems.
    """
    rd = get_reasons_data(location)
    if not rd:
        raise Exception("Reasons data was empty")


def get_reasons_data(location:Optional[str]=None)->dict:
    """Get the reasons data.

    `get_reasons_data()` will attempt to get the data from GS only
    once. If it fails it will cache a "LOAD FAILED" result that will
    cause it to fail when called further in the execution. This is to
    avoid repeted API calls to the GS bucket.

    `location` should be a GS bucket in the form
    gs://bucketname/some/key/reasons.json. If location is not
    provided the env var REASONS_GS_URL will be used and if that
    doesn't exist a default value for the URL will be used.

    This will load from GS once and save in a package level variable.

    If `reasons()` is to be used in an app it makes sense to call
    `get_reasons_data()` when starting that app to ensure the app has
    access and it is configured correctly.

    """
    global _reasons_data
    if _reasons_data is not None:
        return _reasons_data
    if _reasons_data == "LOAD FAILED":
        raise Exception("Previous load of reasons data failed, not trying again "
                        "until _reasons_data is cleared by setting it to None")

    if location is None:
        location = os.environ.get("REASONS_GS_URL", DEFAULT_REASONS_GS_URL)

    if location is None:
        raise ValueError("Must pass location or set env var REASONS_GS_URL")

    blob = None
    try:
        bucket_name = location.strip('gs://').split('/')[0]
        key = '/'.join(location.strip('gs://').split('/')[1:])
        bucket = storage.Client().bucket(bucket_name)
        blob = bucket.get_blob(key)
    except Exception as ex:
        _reasons_data = "LOAD FAILED"
        raise ex

    if not blob:
        _reasons_data = "LOAD FAILED"
        raise Exception(f"Could not get resons file from {location}")

    try:
        with blob.open('r') as fp:
            _reasons_data = json.load(fp)
            return _reasons_data
    except Exception as ex:
        _reasons_data = "LOAD FAILED"
        raise ex


def reasons(id: str, format: FORMATS)-> Optional[str] :
    """
    Find any reasons for inability to process this paper.
    
    Find all the recorded reasons for inability to process this paper (if any),
    that are either general ($id recorded in reasons file with no extension) or
    specific to $format ($id.format recorded in reasons file). If $id includes a
    version number then look for reasons for that specific version or for reasons
    with no version specified.

    We canonicalize the $format from the displayed version in order to look
    up recorded reasons for failure specific to a particular format. Canonical
    forms are: ps, pdf, html, dvi (postscript is converted to ps, all are
    lowercased).

    Returns a list of strings which report reasons for different versions
    or formats fail. List is empty if no reasons are recorded.
    """
    reasons_data = get_reasons_data()

    if not id:
        return None
    if format == 'postscript':
        format = 'ps'

    if id in reasons_data:
        return reasons_data[id]
    if f"{id}.{format}" in reasons_data:
        return reasons_data[f"{id}.{format}"]

    idnov = re.sub(_verregex, '', id)
    has_ver = id != idnov
    if not has_ver:
        return None

    if idnov in reasons_data:
        return reasons_data[idnov]
    if f"{idnov}.{format}" in reasons_data:
        return reasons_data[f"{idnov}.{format}"]
    else:
        return None

