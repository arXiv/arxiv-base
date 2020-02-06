"""
Functions to deal with arxiv package versions.

It can be used in the setup.py file:
 from arxiv.release.dist_version import get_version
 setup(
     version=get_version('arxiv-filemanager'),
     ....
 )
"""
import sys
import pathlib
from subprocess import Popen, PIPE
from datetime import datetime


def get_version(dist_name):
    """Get the version written by write_version(), or the git describe version.

    Parameters
    ----------
    dist_name: str
        Which arxiv distribution to get. ex arxiv-base
        arxiv-filemanager.  These will be mapped to arxiv.base.version
        and arxiv.filemanager.version.

    Returns
    -------
    str
        The version.__version__ value if it exists or the git describe
        version if it exists or the string 'no-git-or-release-version'
    """
    # TODO We might want to make it an error if we are under git
    # and there is a version.py file? It doesn't seem like a good state.
    pkg = '.'.join(dist_name.split('-')) + ".version"
    try:
        name = '__version__'
        dist_version = getattr(__import__(pkg, fromlist=[name]), name)
        return dist_version
    except ModuleNotFoundError:
        pass
    try:
        return get_git_version()
    except ValueError:
        pass
    return 'no-git-or-release-version'


def write_version(dist_name, version):
    """Write the version to a version.py file in a package that corresponds with the dist_name.

    Parameters
    ----------
    dist_name: str
        Which arxiv distribution to get. ex arxiv-base
        arxiv-filemanager.  These will be mapped to arxiv.base.version
        and arxiv.filemanager.version.

    version: str
        A string with a semantic version.

    Returns
    -------
    This returns the path to the version.py file.
    """
    dir = '/'.join(dist_name.split('-')) + "/version.py"
    path = pathlib.Path(dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w+') as ff:  # overwrite existing version
        when = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ff.write("#  Created by tag_check.write_version \n")
        ff.write(f"__when__='{when}'\n")
        ff.write(f"__version__='{version}'\n")
    return path


def get_git_version(abbrev=7):
    """Get the current version using `git describe`."""
    try:
        p = Popen(['git', 'describe', '--dirty', '--abbrev=%d' % abbrev],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip().decode('utf-8')
    except Exception:
        raise ValueError("Cannot get the version number from git")


# Below is intended to let this module be used in CI scripts:
# ``export APP_VER=$(python -m arxiv.release.get_version arxiv-hatsize-agent)``
if __name__ == '__main__':
    print(get_version(sys.argv[1]))
