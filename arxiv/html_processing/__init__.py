import re
from typing import Tuple, Callable
import arxiv.document.exceptions
from arxiv.identifier import Identifier, IdentifierException
from arxiv.document.metadata import DocMetadata
from arxiv.files import FileObj, FileTransform
from flask import render_template, url_for

class HTMLFileTransform(FileTransform):
    """ A stateful `FileTransform` that applies HTML post-processing and branding to HTML papers.
        We track the state of the HTML asset being transformed in this object, to minimize regex overhead.

        Note: Depends on DB access to get metadata for licensing header.
    """
    def __init__(self, file: FileObj, transform_fn: Callable[[bytes, str, DocMetadata], Tuple[str, bytes]], abs_meta: DocMetadata):
        self.fileobj = file
        self.transform_fn = transform_fn
        self.abs_meta = abs_meta
        self.transform_state = 'head' # initial transform state

    def transform(self, data: bytes) -> bytes:
        (new_state, new_data) = self.transform_fn(data, self.transform_state, self.abs_meta)
        self.transform_state = new_state
        return new_data

# This is a stateless transform that can insert scaffolding at the usual global markup transition points.
def render_branded_html_paper(byte_line:bytes, state: str, abs_meta: DocMetadata) -> Tuple[str, bytes]:
    """ We brand and post-process the latexml-generated HTML asset, to allow for change management
        of branded materials within arxiv-browse itself.
        
        The HTML assets from latexml include a single versioned CSS and JS asset, each of which served
        from browse, and coordinated with a LaTeXML version/release. Logic depending on latexml markup
        belongs either in latexml, in our conversion worker or in the CSS/JS assets, not here.

        arXiv-branded headers, footers, etc are added here.
    """
    match state:
        case 'noop':
            # once in noop state, we remain there
            return (state, byte_line)
        case 'head':
            if re.search(b'</head>$', byte_line, re.I):
                # insert new head mixins before </head>
                return ('head_end', \
                    render_template("dissemination/html_scaffold_head_mixins.html", abs_meta=abs_meta)
                    .encode('utf-8') + byte_line)
            elif re.match(b'<(link|script) ', byte_line, re.I) and \
                re.search(b'(?:addons_new|bootstrap\.bundle\.min|html2canvas\.min|feedbackOverlay)\.js', byte_line):
                # pre 02.2026, we used JS rewrites and just returned the GCP bucket HTML content directly
                # For backwards compatibility: when encountering those cases, ABORT REWRITE (noop state)
                return ("noop", byte_line)
            else:
                # pass through all other lines unmodified
                return (state, byte_line)
        case 'head_end':
            if re.match(b'<body>', byte_line, re.I):
                return ('body', \
                    byte_line + render_template("dissemination/html_scaffold_header.html",
                                                 abs_meta=abs_meta)
                    .encode('utf-8'))
            else: # continue until we find <body>
                return (state, byte_line)
        case 'body':
            if re.match(b'\s*<div class="ltx_page_content"', byte_line, re.I):
                # add the licensing infobox at the start of the document content.
                return ('body_content', \
                    render_template("dissemination/html_scaffold_callout_license.html", abs_meta=abs_meta)
                    .encode('utf-8') + byte_line)
            else:
                return (state, byte_line)
        case 'body_footer': # skip the original latexml footer, we render an arXiv one
            if re.search(b'</footer>$', byte_line, re.I):
                return ('body_content', b'') # skipping completed.
            else: 
                return ('body_footer', b'')
        case 'body_content':
            if re.match(b'<footer', byte_line, re.I):
                return ('body_footer', b'')
            elif re.match(b'</body>', byte_line, re.I):
                return ('body_end', \
                    render_template("dissemination/html_scaffold_footer.html", abs_meta=abs_meta)
                    .encode('utf-8') + byte_line)
            else:
                return (state, byte_line)
        case _:
            # pass through all other lines unmodified
            return (state, byte_line)