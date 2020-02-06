# Dealing with versions from git tags

This contains functions for dealing with versions from git tags. They
are intended for use in continuous integration tools.

The general idea is to get the version from the git tag when making a
package or docker image. Out side of these cases the version is from
`git describe` to provide an accurate description of the version and
changes.

## Goals

1. Reduce human error. We have had problems with making a new version
   of a repo but missing the task of setting a new version in files
   like arxiv/base/config.py or in setup.py.
2. Have one source of the version. The git tag is saved to a
   version.py file and that is used in setup.py and
   arxiv/SOMEPKG/version.py. 
3. Versions on web pages should be correct. On non-production web
   pages use 0.15.8 if loaded from a pypi package or docker image, or
   something like 0.15.8-48-dirty if from a git repo.
4. Keep the version out of source code. This information is outside of
   the source code and lives in the source control system. This is
   natural when there is a build step but python lacks one. In python
   the version can be picked up from git at app start up. When
   building a package to upload to pypi, the source is combined with
   the version from the source control system to produce the
   derivative package artifact.

## Do not check in any generated version.py files
These are not intended to be in the source code. They are only
intended to be in released sdist pacakges.
   
## Use in travis-ci 
```yaml
language: python
...
script:
- pip install pipenv
- pipenv install --dev
- pipenv run nose2 -s arxiv --with-coverage

# This will die if there is a tag and it bad
# otherwise a version.py file is created
- pipenv run python -m arxiv.release.tag_check arxiv-base

deploy:
- provider: pypi
 user: arxiv
 password:
   secure: Hz66...n0DDKwN3zsi1k=
 distributions: sdist

 # Here we upload to pypi if we are on a git tag
 # The sdist gets version.py
 on: 
   tags: true
```

## Get the version in app code
```python
from arxiv.release.dist_version import get_version
print(f"arxiv base version: {get_version('arxiv-base')}"
      f"arxiv browse version {get_version('arxiv-browse')}")
```
