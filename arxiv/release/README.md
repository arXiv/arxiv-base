# Get the version in app code
```python
from arxiv.release.dist_version import get_version
print(f"arxiv base version: {get_version('arxiv-base')}"
      f"arxiv browse version {get_version('arxiv-browse')}")
```

# How to set the version

To set the version, tag the commit you want a version on. The version
will then be the continuous integration tools from git tags. 

Outside of the continuous integration tools, if there is no tag, this
will fall back to the result from `git describe`.

# How to setup travis-ci to set versions
```yaml
language: python
. . .
script:
- pip install pipenv
- pipenv sync --dev
- pipenv run nose2 -s arxiv --with-coverage

# This will die if there is a tag and it is bad.
# All good tags get a version.py file.
# This will do nothing if there is no tag.
- pipenv run python -m arxiv.release.tag_check arxiv-browse

deploy:
- provider: pypi
 user: arxiv
 password:
   secure: Hzxyz12345=
 distributions: sdist

 # Here we upload to pypi if we are on a git tag and
 # the sdist gets version.py built during tag_check
 on: 
   tags: true
```

## Do not check in any generated version.py files
These are not intended to be in the source code. They are only
intended to be in released sdist pacakges.

# What format for versions
Tags in github should be in the PEP440 "python public version" format.
https://www.python.org/dev/peps/pep-0440/
Some examples from that page:
0.1 
0.2 
1.0 
1.1 
1.1.0
1.1.1
1.1.2
1.2.0
1.0a1
1.0a2
1.0b1
1.0rc1
1.1a1
1.0.dev1
1.0.dev2
1.0.dev3
1.0.dev4
1.0c1
1.0c2
1.0.post1
1.1.dev1

# General plan for tags and versions
The general idea is to have a single source for the version. This is
from the git tag when building a package to upload to PyPI. 

Outside of these cases the version is from `git describe` to provide
an accurate description of the version and local changes.

## Goals

1. Make it easy for developers working on the project to make new
   versions of packages from git repos. The CI system can do it so
   individual developers don't need PyPI accounts, and they don't need
   to have their PyPI accounts added to each arxiv package.
1. Reduce human error. We have had problems with making a new version
   of a repo but missing the task of setting a new version in files
   like arxiv/base/config.py or in setup.py. This allows us to
   automatically set the version from the git tag.
2. Have one source of the version. The git tag is saved to a
   version.py file and that is used in setup.py and
   arxiv/SOMEPKG/version.py.
3. Avoid hardcoded versions in web pages. We have had problems where
   the version gets hardcoded in a config file and never updated,
   especially for point, patch and build releases. 
4. Keep the version out of source code. Version information belongs in
   the source control system. This is natural when there is always a
   build step but python often lacks one. In python the version can be
   picked up from git at app start up. When building a package to
   upload to pypi, the source is combined with the version from the
   source control system to produce the derivative package artifact.

## How the version is set and found

### If I install a package from PyPY
1. Someone tags a commit in github to arxiv-shoehorn
2. Travis-ci builds that commit, with the tag in TRAVIS_TAG
3. The travis step ```python -m arxiv.release.tag_check
   arxiv-shoehorn``` picks up the tag. If it is a valid python public
   version, it gets written to the file ```arxiv/shoehorn/version.py```.
4. Travis-ci uploads the built python package to PyPI. This version.py
   file is includded in that upload.
5. When someone installs that package from PyPI,
   ```arxiv.release.dist_version.get_version('arxiv-shoehorn')``` will
   first check the version.py file and return the version from that.

### If I install a package with pip install -e ../somegitclone
In this case there is no version.py file

1. You checkout arxiv-subproj and create a virtual env for it.
2. Then you do ```cd ~/workspace/arxiv-subproj; pipenv install; pipenv shell```
3. You then checkout ```~/workspace/arxiv-base```
4. Now you want install arxiv-base to arxiv-subproj in develop mode so you do
   ```pip install -e ../arxiv-base```
5. During that install setup.py runs and uses
   ```arxiv.release.dist_version.get_version('arxiv-base')```
6. ```get_version()``` finds no version.py file, and it finds no
   ```pkg_resources``` version
7. So get_version() trys to run ```git describe --dirty``` and that
   works since it is in a git check
8. setup.py uses the git describe value as the package version during the install.
9. arxiv.release.dist_version.get_version() will first check the
   version.py file and find nothing, then it will check the
   pkg_resources and find a version there and return that.

### If I'm working in a git cloned directory
You might checkout a git repo like arxiv-browse and run the flask app in
that.

1. You git clone ~/workspace/arxiv-browse. 
2. You do ```pipenv install```
3. You run the flask app
4. Flask runs config.py and it has ```BROWSE_VERSION =
   get_version('arxiv-browse')```
5. ```get_version('arxiv-browse')``` checks arxiv.browse.version and
   nothing is there, it checks the pkg_resources and nothing is there,
   it runs ```git describe``` and gets a value from there.

## The version.py file
This is the solution we arrived at after fiddling with these parts. It
might be possible to eliminate the version.py files.

The setup.py could get the version from git and ```get_version``` could get
it from ```pkg_resources``` or from git describe.
