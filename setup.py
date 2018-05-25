"""Install arXiv-base as an importable package."""

from setuptools import setup, find_packages


setup(
    name='arxiv-base',
    version='0.7.1',
    packages=find_packages(exclude=['tests.*']),
    zip_safe=False,
    include_package_data=True
)
