import jinja2

def browse_template_loader():
    """Returns a Jinja2 Template loader that will load arxiv.browse.templates"""
    return jinja2.PackageLoader('arxiv.browse', 'templates')
