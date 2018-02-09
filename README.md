# arXiv Base

This project provides a base Flask application and base Docker image for
arXiv-NG services.

Each component of this project **must** meet all of the following criteria:

1. It is likely that the component will be utilized in many or all arXiv
   services.
2. Once stable, it is unlikely to change often.
3. It is unlikely that implementing new features in specific services
   would require changes to the component.
4. When a component does change, it **must** change in the same way for all of
   the services that use it.

## Base CSS and Templates for arXiv.org-NG

Templates are written in [Jinja2 syntax](http://jinja.pocoo.org/docs/2.9/). CSS
framework is [Bulma](http://bulma.io) with arXiv-specific overrides for color
and typography. While the .sass format has been used for override files, .scss
files may also be imported and included.

These files set the default display styles and layout for all pages on
arxiv-NG, and can be overridden as needed by submodules.

**TODO:** Add autoprefixer in postcss and autocompile sass/scss

testpage.html is included for rapid evaluation of display layer CSS without
invoking a local environment to render templates.

## Development server

This project includes a minimal Flask application for development
verification/testing purposes. To run the dev server (assuming that you are
working in the root of this repository):

```bash
$ FLASK_APP=app.py FLASK_DEBUG=1 flask run
```

You should be able to view the rendered ``testpage.html`` at
``http://127.0.0.1:5000/test``.

## Flask

To use the base UI package in a Flask application...

Add it to your ``requirements.txt`` file. For the time being, we'll
distribute directly from GitHub. To use a specific version, for example, you
would write:

``-e git://github.com/cul-it/arxiv-base.git@0.1#egg=arxiv-base``

Or if this repo is private, and you want to install a specific commit:

``-e git+ssh://git@github.com/cul-it/arxiv-base.git@d9af6c670afdf6f0fda6d92f7b110dcd60514f4a#egg=arxiv-base``

See the [pip documentation](https://pip.pypa.io/en/latest/reference/pip_install/#git)
for details.

In your application factory, instantiate the BaseUI blueprint. This makes
templates and static files available to you. For example, in your
``factory.py`` module:

```python
from flask import Flask
from arxiv.base import Base
from someapp import routes


def create_web_app() -> Flask:
   app = Flask('someapp')
   app.config.from_pyfile('config.py')

   Base(app)   # Registers the base/UI blueprint.
   app.register_blueprint(routes.blueprint)    # Your blueprint.
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

## Editing and compiling sass

The file arxivstyle.css should never be edited directly. It is compiled from arxivstyle.sass with this command from project directory root:
```sass base/static/sass/arxivstyle.sass:base/static/css/arxivstyle.css```

or you can use the ``--watch`` option to autocompile on any changed file:

```sass --watch base/static/sass/arxivstyle.sass:baseui/static/css/arxivstyle.css```

Bulma source files are included in the ``static/sass`` directory so that variables can be overridden directly during compile. The ``arxivstyle.sass`` file has been written to do this; do not edit it.

[Documentation for sass](http://sass-lang.com/documentation/file.SASS_REFERENCE.html)
