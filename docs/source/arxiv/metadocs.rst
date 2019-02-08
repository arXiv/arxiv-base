Meta-documentation: How to create documentation
=================================================

This guide shows:

1.  Adding Sphinx and extensions to a Pipfile.
2.  Configuring docs using sphinx-quickstart.
3.  Testing Sphinx.
4.  Creating auto-doc stubs.
5.  Configuring GitHub pages.

Adding Sphinx to the Pipfile
''''''''''''''''''''''''''''''

Add the following to the Pipfile's ``[dev-packages]`` section::

    [dev-packages]
    sphinx = "*"
    sphinx-autodoc-typehints = "*"

Install Sphinx to the pipenv::

    pipenv install --dev

Add the docs/_build directory to the .gitignore::

    docs/_build

Make and change to a docs directory::

    mkdir docs
    cd docs

Configuring Sphinx::

    Execute "pipenv run sphinx-quickstart" from your project's "docs" directory and use the defaults except:
        Separate source and build directories: NO
        Project name: Enter your project name (e.g., arXiv Compilation Service)
        Author name(s): arXiv-NG Team
        Project release: 0.1 (or whatever your version number is
        autodoc: y
        intersphinx: y
        coverage: y
        viewcode: y
        githubpages: y
        Create Makefile? y

    git add Makefile conf.py index.rst

    git commit -m "initial sphinx commit"

``git status`` should then show a clean working tree.

Testing Sphinx
''''''''''''''''

Since the docs necessitate access to the packages to generate documentation, you must run it with the pipenv activated. There are ways to run the commands with ``pipenv run`` but the relative paths can get messed up.

I prefer to use the following method::

    pipenv shell
    cd docs
    make html
    exit

After this, the docs should be created. in the _build folder. Open "docs/_build/index.html" to see what it made.

Creating auto-doc stubs
'''''''''''''''''''''''''
For each module you will create an rst file containing the automod declarations.

For example, with arxiv-compiler, I would create a file "compiler.domain.rst".

.. code-block:: none
    :caption: compiler.domain.rst

    compiler.domain module
    =========================
    
    .. automodule:: compiler.domain
        :members:
        :undoc-members:
        :show-inheritance: 

After creating this file, I add it to the index.rst so it builds.

.. code-block:: none
    :caption: index.rst

    .. arXiv Compilation Service documentation master file, created by
    sphinx-quickstart on Mon Oct 15 16:35:18 2018.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.
    
    Welcome to arXiv Compilation Service's documentation!
    =====================================================
    
    .. toctree::
    :maxdepth: 2
    :caption: Contents:
    
    compiler.domain.rst
    
    
    
    Indices and tables
    ==================
    
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

If you have an issue with ModuleNotFoundError, then the paths in the conf.py need to be changed. Add the following to the top of docs/conf.py:

.. code-block:: python
    :caption: conf.py

    import os
    import sys
    sys.path.insert(0, os.path.abspath('.'))
    sys.path.append(os.path.abspath('..'))

Configuring GitHub pages
''''''''''''''''''''''''''
GitHub Pages integration requires creating a new "orphan" branch that does not have the history of the rest of the project. This branch is called "gh-pages". The logistics of maintaining an active development environment and this totally detached gh-pages branch is complicated, especially if you have untracked files or files that are explicitly in the .gitignore of the code branches.

In order to manage the complications of the gh-pages branch, the following bash script can be used to initialize or update documentation on GitHub Pages.

Two configuration settings should be changed:

1.  The REPO parameter
2.  Double check that SRCDOCS reflects your project structure (some use `pwd`/docs/build rather than `pwd`/docs/_build)

The script should be run from your development copy's repository root (same level as README.md). Before running, activate your pipenv shell::

    pipenv install --dev
    pipenv shell
    bash update-docs.sh

.. code-block:: bash
    :caption: update-docs.sh

    #!/bin/bash
    SRCDOCS=`pwd`/docs/_build/html
    REPO=cul-it/arxiv-compiler
    echo $SRCDOCS

    cd `pwd`/docs
    make html

    cd $SRCDOCS
    MSG="Adding gh-pages docs for `git log -1 --pretty=short --abbrev-commit`"

    TMPREPO=/tmp/docs/$REPO
    rm -rf $TMPREPO
    mkdir -p -m 0755 $TMPREPO
    echo $MSG

    git clone git@github.com:$REPO.git $TMPREPO
    cd $TMPREPO

    ## checkout the branch if it exists, if not then create it and detach it from the history
    if ! git checkout gh-pages; then
        git checkout --orphan gh-pages
        git rm -rf .
        touch .nojekyll
        git add .nojekyll
    else
        git checkout gh-pages  ###gh-pages has previously one off been set to be nothing but html
    fi

    cp -r $SRCDOCS/* $TMPREPO
    git add -A
    git commit -m "$MSG" && git push origin gh-pages
