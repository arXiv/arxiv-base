# Base CSS and Templates for arXiv.org-NG

Templates are written in [Jinja2 syntax](http://jinja.pocoo.org/docs/2.9/). CSS
framework is [Bulma](http://bulma.io) with arXiv-specific overrides for color
and typography. While the .sass format has been used for override files, .scss
files may also be imported and included.

These files set the default display styles and layout for all pages on
arxiv-NG, and can be overridden as needed by submodules.

Currently there are no compile procedures or dependencies associated with these
files.

**TODO:** Add autoprefixer in postcss and autocompile sass/scss
**TODO:** Add override variables prior to Bulma compile so that we can take
advantage of its derived variables

testpage.html is included for rapid evaluation of display layer CSS without
invoking a local environment to render templates.

## Flask

To use the base UI package in a Flask application...

Add it to your ``requirements.txt`` file. For the time being, we'll
distribute directly from GitHub. To use a specific version, for example, you
would write:

``-e git://github.com/cul-it/arxiv-base-ui.git@0.1#egg=arxiv-base-ui``

See the [pip documentation](https://pip.pypa.io/en/latest/reference/pip_install/#git)
for details.

In your application factory, instantiate the BaseUI blueprint. This makes
templates and static files available to you. For example, in your
``factory.py`` module:

```python
from flask import Flask
from baseui import BaseUI
from someapp import routes


def create_web_app() -> Flask:
   app = Flask('someapp')
   app.config.from_pyfile('config.py')

   BaseUI(app)   # Registers the base UI blueprint.
   app.register_blueprint(routes.blueprint)    # Your blueprint.
return app
```

You can now extend base templates, e.g.:

```html
{%- extends "baseui/base.html" %}

{% block content %}
Hello world!
{% endblock %}
```

And use static files in your templates, e.g.:

```
{{ url_for('baseui.static', filename='images/CUL-reduced-white-SMALL.svg') }}
```
