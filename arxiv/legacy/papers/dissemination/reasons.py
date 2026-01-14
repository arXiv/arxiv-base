"""Reasons that some papers cannot produce formats.

The function `get_reasons_data()` in this package depends on access to
`DEFAULT_REASONS_GS_URL` in google storage.
"""

from typing import Optional, Literal
import re
import os
import json

from google.cloud import storage

from arxiv.files import FileObj

FORMATS = Literal["ps", "pdf", "html", "dvi", "postscript"]

DEFAULT_REASONS_GS_URL = "gs://arxiv-production-data/reasons.json"

_verregex = re.compile(r"v\d+$")

_reasons_data = None


def get_reasons_data(file: FileObj) -> dict:
    """Get the reasons' data.

    `get_reasons_data()` will attempt to get the data from GS only
    once. If it fails it will cache a "LOAD FAILED" result that will
    cause it to fail when called further in the execution. This is to
    avoid repeted API calls to the GS bucket.

    `location` should be `FileObj` like
    gs://arxiv-production-data/reasons.json.

    This will load once and save in a package level variable.

    If `reasons()` is to be used in an app it makes sense to call
    `get_reasons_data(file)` when starting that app to ensure the app has
    access and it is configured correctly.
    """
    global _reasons_data
    if _reasons_data is not None:
        return _reasons_data
    if _reasons_data == "LOAD FAILED":
        raise Exception(
            "Previous load of reasons data failed, not trying again "
            "until _reasons_data is cleared by setting it to None"
        )
    try:
        with file.open("r") as fp:
            _reasons_data = json.load(fp)
            return _reasons_data
    except Exception as ex:
        _reasons_data = "LOAD FAILED"
        raise ex


def reasons(reasons_data: dict, id: str, format: FORMATS) -> Optional[str]:
    """Find any reasons for inability to process this paper.

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

    See test_reasons.py for an example of the JSON needed for `reasons_data`.
    """

    if not id:
        return None
    if format == "postscript":
        format = "ps"

    if id in reasons_data:
        return reasons_data[id]
    if f"{id}.{format}" in reasons_data:
        return reasons_data[f"{id}.{format}"]

    idnov = re.sub(_verregex, "", id)
    has_ver = id != idnov
    if not has_ver:
        return None

    if idnov in reasons_data:
        return reasons_data[idnov]
    if f"{idnov}.{format}" in reasons_data:
        return reasons_data[f"{idnov}.{format}"]
    else:
        return None
