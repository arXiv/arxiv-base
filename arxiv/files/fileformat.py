"""Format for use with an ItemSource."""
"""tar.gz, gzipped postscript, gzipped html, a single PDF file, a gzip that is
not tarred, a single dox file, a single odt file."""

from typing import Optional


class FileFormat():
    def __init__(self, id:str, content_encoding:Optional[str], content_type:str)->None:
        self.id = id
        self.content_encoding = content_encoding
        self.content_type = content_type

    def __repr__(self) -> str:
        return self.id



targz = FileFormat("targz", "gzip", "application/gzip")
tex = FileFormat("tex", "gzip",  "application/x-latex")
psgz = FileFormat("psgz", "gzip", "application/gzip")
dvigz = FileFormat("dvigz", "gzip", "application/gzip")
htmlgz = FileFormat("htmlgz", "gzip", "application/gzip")
pdf = FileFormat("pdf", None, "application/pdf")
pdftex = FileFormat("pdftex", "gzip", "application/x-latex")
ps = FileFormat("ps", None, "application/postscript")
gz = FileFormat("gz", "gzip", "application/gzip")
docx = FileFormat("docx", "gzip", "application/gzip") #these files get downloaded in a tarball with a pdf version of them
html = FileFormat("html","utf-8", "text/html")

formats = {
    "targz": targz,
    "tex": tex,
    "psgz": psgz,
    "dvigz": dvigz,
    "htmlgz": htmlgz,
    "pdf": pdf,
    "pdftex": pdftex,
    "ps": ps,
    "gz": gz,
    "docx": docx,
    "html": html
    }
