"""Install arXiv-base as an importable package."""

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

    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)

    try:
        p = Popen(['git', 'describe', '--dirty'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip().decode('utf-8')
    except Exception:
        raise ValueError("Cannot get the version number from git")
    raise RuntimeError("Unable to find version string.")

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
        'bleach==3.1.0',
        'backports-datetime-fromisoformat==1.0.0',
        'typing-extensions'
    ],
    include_package_data=True
)
