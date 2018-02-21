from setuptools import setup, find_packages


setup(
    name='arxiv-base',
    version='0.2.2',
    packages=find_packages(exclude=['tests.*']),
    zip_safe=False,
    include_package_data=True
)
