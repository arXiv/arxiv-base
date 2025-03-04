# arXiv Base

This project provides a base Flask application and base Docker image for
arXiv-NG services.

Each component of this project **must** meet all the following criteria:

1. It is likely that the component will be utilized in many or all arXiv
   services.
2. Once stable, it is unlikely to change often.
3. It is unlikely that implementing new features in specific services
   would require changes to the component.
4. When a component does change, it **must** change in the same way for all    the services that use it.

## Base CSS and Templates for arXiv.org-NG

Templates are written in [Jinja2 syntax](http://jinja.pocoo.org/docs/2.9/). CSS
framework is [Bulma](http://bulma.io) with arXiv-specific overrides for color
and typography. While the .sass format has been used for override files, .scss
files may also be imported and included.

These files set the default display styles and layout for all pages on
arxiv-NG, and can be overridden as needed by submodules.

A template is included for rapid evaluation of display layer CSS within this
repo, prepopulated with sample content.
The ``styleguide.html`` template (route: /styleguide) shows error message
samples, informational message boxes, and sample content from search.

## Development server

This project includes a minimal Flask application for development
verification/testing purposes. To run the dev server (assuming that you are
working in the root of this repository):

```bash
poetry install
$ FLASK_APP=app.py FLASK_DEBUG=1 poetry run flask run
```

You should be able to view the rendered ``styleguide.html`` at
``http://127.0.0.1:5000/styleguide``.

## Installing `arxiv-base`

To use the base package in a Flask application add it to your
dependency manager.  To use a specific version, for example, you would write:

``arxiv-base = "==0.11.1rc5"``

Or if you want to install a specific working branch (dev only) the line
might read:

``arxiv-base = {git = "https://github.com/arXiv/arxiv-base.git@task/ARXIVNG-1215"}``

You can use ``pip`` from the command line to install a selected
unpublished branch. First uninstall existing, then reinstall using pip
syntax above.  Example:

```bash
pip uninstall arxiv-base
pip install git+https://github.com/arXiv/arxiv-base.git@task/ARXIVNG-1010#egg=arxiv-base
```

## Using `arxiv-base` with Flask

In your application factory, instantiate the Base component. This makes
templates and static files available to you. For example, in your
``factory.py`` module:

```python
from flask import Flask
from arxiv.base import Base

def create_web_app() -> Flask:
   app = Flask('mega_tool')
   app.config.from_pyfile('config.py')

   Base(app)   # Registers the base/UI blueprint.
   @app.route("/mega_tool")
   def mega_tool():
       # TODO use something from arxiv-base 
       return "<p>Mega_tool!</p>"

   return app
```

You can now extend base templates, e.g.:

```html
{%- extends "base/base.html" %}

{% block content %}
Hello world!
{% endblock %}
```

And use static files in your templates, e.g.:

```
{{ url_for('base.static', filename='images/CUL-reduced-white-SMALL.svg') }}
```

## Static files and paths

In order to serve static assets for multiple versions of the app at
the same time, arxiv-base prefixes the app name and app version to
asset urls. This is to allow gracefully upgrades with no broken links
to css, js or images.

The ``Base`` component will automatically set your app's
[``static_url_path``](http://flask.pocoo.org/docs/1.0/api/#flask.Flask.static_url_path)
using the name of the app and the value of ``APP VERSION`` in your
config to ``/static/[app name]/[ app version ]``. It will also rewrite
blueprint
[``static_url_path``](http://flask.pocoo.org/docs/1.0/api/#flask.Blueprint.static_url_path)
to ``/static/[app name]/[ app version ]/[ blueprint name]``.

### Serving static files on S3
We use [Flask-S3](https://flask-s3.readthedocs.io/en/latest/) to serve static
files via S3. To deploy the assets for the current version:

  pip install ./
  AWS_ACCESS_KEY_ID=x \
  AWS_SECRET_ACCESS_KEY=x+3RcGf1Oul66cwSJbZZcdZdEv0ZC9ax2 \
  AWS_REGION=us-east-1 FLASKS3_BUCKET_NAME=arxiv-web-static1 \
  python upload_static_assets.py

Be sure to initialize the integration after instantiating ``Base`` and
registering your blueprints. For example:

```python
# TODO just have a s3 script
# def create_web_app() -> Flask:
#     """Initialize and configure the application."""
# 
#     app = Flask('cool_app')
#     app.config.from_object(config)
#     Base(app)    # Gives us access to the base UI templates and resources.
#     app.register_blueprint(routes.blueprint)
#     s3.init_app(app)    # <- Down here!
#     return app
```

## App tests

Some tests to check app configuration and pattern compliance are provided in
``arxiv.base.tests``. See that module for usage. You can run them with the command ``pytest``

## Editing and compiling sass

The file `arxivstyle.css` should never be edited directly. It is compiled from
`arxivstyle.sass` with this command from project directory root:
``sass arxiv/base/static/sass/arxivstyle.sass:arxiv/base/static/css/arxivstyle.css``

or you can use the ``--watch`` option to autocompile on any changed file:

``sass --watch arxiv/base/static/sass/arxivstyle.sass:arxiv/base/static/css/arxivstyle.css``

Bulma source files are included in the ``static/sass`` directory so that
variables can be overridden directly during compile. The ``arxivstyle.sass``
file has been written to do this; do not edit it.

[Documentation for sass](http://sass-lang.com/documentation/file.SASS_REFERENCE.html)

## Layout features, tips and tricks

### Beta watermark

Adding ``class="beta"`` to the main content div will create a beta watermark at
 the top left of pages having this class.

## Upload to pypi

```bash
pip install --upgrade setuptools wheel twine
python setup.py sdist bdist_wheel
twine --upload dist/*  # Enter username and password from lastpass
```
