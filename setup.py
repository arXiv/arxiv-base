"""Install arXiv-base as an importable package.

This needs to be able to install from a directory that has a
version.py file or from a directory that has no version file but does
have git

To test with no version but with git:
```
$ cd tmp
$ git clone git@github.com:arXiv/arxiv-base.git
$ cd arxiv-base
$ pip install ./
...
$ pip show arxiv-base | grep Version
Version: 0.16.6.2-dev-3-ga5af154 
```

To test with a version file but no git:
```
$ cd tmp
$ git clone git@github.com:arXiv/arxiv-base.git
$ cd arxiv-base
$ rm -rf .git
$ python 
Python 3.6.9 (default, Dec 23 2019, 12:56:30)[GCC 7.4.0] on linux
>>> import arxiv.release.dist_version
>>> arxiv.release.dist_version.write_version('arxiv-base', '10.9.9')
CTRL-D
$ pip install ./
...
$ pip show arxiv-base | grep Version
Version: 10.9.9
```

"""

import codecs
import os
import sys
import re
from subprocess import Popen, PIPE

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    try:
        version_file = read(*file_paths)
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
        if version_match:
            return version_match.group(1)
    except Exception:
        pass # no file is find, just try to get it from git

    try:
        p = Popen(['git', 'describe', '--dirty'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip().decode('utf-8')
    except Exception:
        raise RuntimeError("Unable to find version string in version file or git. See setup.py for instructions.")


setup(
    name='arxiv-base',
    version=find_version('arxiv', 'base', 'version.py'),
    packages=[f'arxiv.{package}' for package
              in find_packages('arxiv', exclude=['*test*'])],
    zip_safe=False,
    install_requires=[
        'flask',
        'jsonschema',
        'pytz',
        'uwsgi',
        'boto3',
        'bleach==3.3.0',
        'backports-datetime-fromisoformat==1.0.0',
        'typing-extensions'
    ],
    include_package_data=True
)
