"""Functions to ensure git tag version is correct for travis and to get ver.

This is intended as a check to use in travis ci.

This will look to see if there is a TRAVIS_TAG env var,
if there is it means we have a tag in the CI system.

It will check that tag to see if it is a valid public python version
that pypi will accept.

If it is valid, it will make a version.py file.

If there is no TRAVIS_TAG or it is invalid, this will do nothing.

Invalid tags should be prevented from getting into pypi by pypi
just rejecting the upload.

It can be used in a travis.yml:
script:
- pip install arxiv-base
- python deploy/prepare_for_version.py


This can also be used to check if a version string is valid:
``TRAVIS_TAG=0.2.3-somethingX python -m arxiv.release.tag_check arxiv-base``

This does not write or update a RELEASE-VERSION file.
"""


from typing import Any
import sys
import os
import re
from .dist_version import write_version

NO_TAG_MSG = (
    "OK: Skipping publish version check since no git tag found in TRAVIS_TAG"
)

REGRESSIVE_MSG = "NOT OK: Tag did not pass tag check"
INVALID_MSG = "OK: skipping publish version since the tag is not a valid PEP440 public python version. See https://www.python.org/dev/peps/pep-0440/#version-scheme"


def prepare_for_version(dist_name: str) -> Any:
    """Prepare for a version on travis-ci.

    Intended to be used when prepareing a version on travis-ci or
    other CI. This will check if a tag exists and verify it is
    good. Then it will write the version to a python file that will be
    used by both the app code and setup.py.

    This does not check if the tag is redundent since by the time travis
    runs anything, the tag will already be in git.
    """
    tag_to_publish = os.environ.get("TRAVIS_TAG", None)

    if not tag_to_publish:
        print(NO_TAG_MSG)
        return 0

    if not is_valid_python_public_version(tag_to_publish):
        print(INVALID_MSG)
        return 0

    topkg = write_version(dist_name, tag_to_publish)
    print(f"Wrote version {tag_to_publish} to {topkg}")


def is_valid_python_public_version(tag: str) -> bool:
    """Check if tag is valid PEP440 public python version."""
    return bool(_pep440public_ver.match(tag))


# Patern from PEP440 with local removed
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
"""

_pep440public_ver = re.compile(
    r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE,
)

if __name__ == "__main__":
    """ This is intended to let this module be used in CI scripts:
    ``python -m arxiv.release.tag_check``
    """
    prepare_for_version(sys.argv[1])
