"""Install arXiv-base as an importable package."""

from setuptools import setup, find_packages
from arxiv.release.dist_version import get_version

setup(
    name='arxiv-base',
    version=get_version('arxiv-base'),
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
