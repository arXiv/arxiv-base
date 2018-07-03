"""Install arXiv-base as an importable package."""

from setuptools import setup, find_packages

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

pfile = Project(chdir=False).parsed_pipfile


setup(
    name='arxiv-base',
    version='0.8.1',
    packages=[f'arxiv.{package}' for package
              in find_packages('arxiv', exclude=['*test*'])],
    zip_safe=False,
    install_requires=convert_deps_to_pip(pfile['packages'], r=False),
    include_package_data=True
)
