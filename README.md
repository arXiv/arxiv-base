#Base CSS and Templates for arXiv.org-NG

Templates are written in [Jinja2 syntax](http://jinja.pocoo.org/docs/2.9/).
CSS framework is [Bulma](http://bulma.io) with arXiv-specific overrides for color and typography.
While the .sass format has been used for override files, .scss files may also be imported and included.

These files set the default display styles and layout for all pages on arxiv-NG,
and can be overridden as needed by submodules.

Currently there are no compile procedures or dependencies associated with these files.
**TODO:** Add autoprefixer in postcss and autocompile sass/scss
**TODO:** Add override variables prior to Bulma compile so that we can take advantage of its derived variables

testpage.html is included for rapid evaluation of display layer CSS without invoking a local environment to render templates.
