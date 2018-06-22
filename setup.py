"""Install arXiv-base as an importable package."""

from setuptools import setup, find_packages


setup(
    name='arxiv-base',
    version='0.8.1',
    packages=[f'arxiv.{package}' for package
              in find_packages('arxiv', exclude=['*test*'])],
    zip_safe=False,
    include_package_data=True
)
