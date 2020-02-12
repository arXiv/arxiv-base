"""Functions to ensure version of git tag is correct for travis and to get that version.

This is intended as a check to use in travis ci.

It will:
1. Check if there is a git tag on the commit.
2. Check that the tag is a semver
3. Check it aginst all other git tags to avoid duplicates or regressions

It can be used in a travis.yml:
script:
- pip install arxiv-base
- python deploy/prepare_for_version.py


This does not write or update a RELEASE-VERSION file.
"""


from typing import List
from subprocess import Popen, PIPE
import sys
import os
from datetime import datetime
from semantic_version import Version
from .dist_version import get_version, write_version

NO_TAG_MSG = "OK: Skipping publish version check since no git tag found in TRAVIS_TAG"
REGRESSIVE_MSG = "NOT OK: Tag did not pass tag check"


def prepare_for_version(dist_name):
    """Prepare for a version on travis-ci.

    Intended to be used when prepareing a version on travis-ci or
    other CI. This will check if a tag exists and verify it is
    good. Then it will write the version to a python file that will be
    used by both the app code and setup.py.

    This does not check if the tag is redundent since by the time travis
    runs anything, the tag will already be in git.

    This will call sys.exit() if there are problems.

    """
    tag_to_publish = os.environ.get('TRAVIS_TAG', None)
    if not tag_to_publish:
        print(NO_TAG_MSG)
        sys.exit(0)

    # TRAVIS_TAG will already be in existing tags
    existing = git_tags()
    existing.remove(tag_to_publish)

    if is_regressive_version(tag_to_publish, existing):
        print(REGRESSIVE_MSG)
        sys.exit(1)

    topkg = write_version(dist_name, tag_to_publish)
    print(f"Wrote version {tag_to_publish} to {topkg}")


def git_tags():
    """Get all git tags."""
    p = Popen(['git', 'tag'], stdout=PIPE, stderr=PIPE)
    p.stderr.close()
    lines = p.stdout.readlines()
    return [tag.decode('utf-8').strip() for tag in lines]


def tags_to_versions(tags):
    """Convert tags to versions but drop all tags that do not convert."""
    rv = []
    for tag in tags:
        try:
            rv.append(Version.coerce(tag))
        except ValueError:
            pass
    return rv


def is_regressive_version(tag, existing):
    """Check if a tag is regressive."""
    isreg, msg = is_regressive_version_with_msg(tag, existing)
    print(msg)
    return isreg


def is_regressive_version_with_msg(tag: str, existing: List[str]):
    """Check if sver is before any semver in existing."""
    tagsv = Version(tag)
    existing_vers = tags_to_versions(existing)

    def _cmp(a, b):
        return (a > b) - (a < b)

    _, same_major, ahead_major = \
        order_for_level(existing_vers,
                        lambda ex: _cmp(ex.major, tagsv.major))
    if not same_major:
        if not ahead_major:
            return False, f'{tagsv} is a new major'
        else:
            return True, f'{tagsv} regressive major behind {ahead_major[0]}'

    _, same_minor, ahead_minor = \
        order_for_level(same_major,
                        lambda ex: _cmp(ex.minor, tagsv.minor))
    if not same_minor:
        if not ahead_minor:
            return False, f'{tagsv} is a new minor for existing major'
        else:
            return True, f'{tagsv} regressive minor behind {ahead_minor[0]}'

    _, same_patch, ahead_patch = \
        order_for_level(same_minor,
                        lambda ex: _cmp(ex.patch, tagsv.patch))
    if not same_patch:
        if not ahead_patch:
            return False, f'{tagsv} is a new patch for existing minor'
        else:
            return True, f'{tagsv} regressive patch behind {ahead_patch[0]}'

    _, same_pre, ahead_pre = \
        order_for_level(same_patch, lambda ex: _cmp(ex,tagsv))
    if same_pre:
        return True, f'{tagsv} is same as {same_pre[0]}'
    if ahead_pre:
        return True, f'{len(ahead_pre)} versions are ahead of {tagsv}'
    else:
        return False, f'{tagsv}: nothing the same or ahead'


def order_for_level(existing_vers, checker):
    """Get before, same_level and ahead versons using checker."""
    checked = [(ex, checker(ex)) for ex in existing_vers]
    before = [ex for ex, excp in checked if excp < 0]
    same_level = [ex for ex, excp in checked if excp == 0]
    ahead = [ex for ex, excp in checked if excp > 0]
    return before, same_level, ahead


if __name__ == '__main__':
    """ This is intended to let this module be used in CI scripts:
    ``python -m arxiv.release.tag_check``
    """
    prepare_for_version(sys.argv[1])
