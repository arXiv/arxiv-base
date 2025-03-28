"""Shared functions that support determination of dissemination formats."""
import re
from typing import List, Optional, Union, Literal

import logging
import tarfile
from operator import itemgetter
from tarfile import CompressionError, ReadError
from typing import Dict

from ..files import FileObj

logger = logging.getLogger(__name__)

# List of tuples containing the valid source file name extensions and their
# corresponding dissemination formats.
# There are minor performance implications in the ordering when doing
# filesystem lookups, so the ordering here should be preserved.
VALID_SOURCE_EXTENSIONS = [
    ('.tar.gz', []),
    ('.pdf', ['pdfonly']),
    ('.ps.gz', ['pdf', 'ps']),
    ('.gz', []),
    ('.dvi.gz', []),
    ('.html.gz', ['html'])
]
"""List of tuples containing the valid source file name extensions and their
corresponding dissemintation formats.

There are minor performance implications in the ordering when doing
filesystem lookups, so the ordering here should be preserved.
"""


def formats_from_source_file_name(source_file_path: str) -> List[str]:
    """Get list of formats based on source file name."""
    if not source_file_path:
        return []
    for file_ending, format_list in VALID_SOURCE_EXTENSIONS:
        if str(source_file_path).endswith(file_ending) and format_list:
            return format_list
    return []


def formats_from_source_flag(source_flag: str) -> List[str]:
    """Get the dissemination formats based on source type and preference.

    Source file types are represented by single-character codes:
    I - ignore
        All files auto ignore. No paper available.
    S - source encrypted
        Source is encrypted and should not be made available.
    P - PS only
        Multi-file PS submission. It is not necessary to indicate P with single
        file PS since in this case the source file has .ps.gz extension.
    D - PDFlatex
        A TeX submission that must be processed with PDFlatex
    H - HTML submissions
        Multi-file HTML submission.
    A - includes ancillary files
        Submission includes ancillary files in the /anc directory
    B - DC pilot data
        Submission has associated data in the DC pilot system
    X - DOCX
        Submission in Microsoft DOCX (Office Open XML) format
    O - ODF
        Submission in Open Document Format
    F - PDF only
        PDF-only submission with .tar.gz package (likely because of anc files)
    """
    source_flag = source_flag if source_flag else ''
    has_encrypted_source = re.search('S', source_flag, re.IGNORECASE)
    has_ignore = re.search('I', source_flag, re.IGNORECASE)
    if has_ignore:
        if not has_encrypted_source:
            return ['src']
        else:
            return []

    has_ps_only = re.search('P', source_flag, re.IGNORECASE)
    has_pdflatex = re.search('D', source_flag, re.IGNORECASE)
    has_pdf_only = re.search('F', source_flag, re.IGNORECASE)
    has_html = re.search('H', source_flag, re.IGNORECASE)
    has_docx_or_odf = re.search(r'[XO]', source_flag, re.IGNORECASE)

    formats: list[str] = []
    if has_ps_only:
        formats.extend(['pdf', 'ps'])
    elif has_pdflatex:
        formats.extend(['pdf', 'src'])
    elif has_pdf_only:
        formats.extend(['pdf'])
    elif has_html:
        formats.extend(['html'])
    elif has_docx_or_odf:
        formats.extend(['pdf'])
    else:
        formats.extend(['pdf', 'ps', 'src'])

    # other is added for display purposes maybe move to controller or template?
    formats.extend(['other'])
    return formats


SOURCE_FORMAT = Literal["tex", "ps", "html", "pdf", "withdrawn", "pdftex", "docx"]


def get_all_formats(src_fmt: Optional[Union[str, SOURCE_FORMAT]]) -> List[str]:
    """Returns the list of all formats that the given src can be
    disseminated in. Takes sources format and knows what transformations
    can be applied.

    Does not include sub-formats (like types of ps).
    """
    match src_fmt:
        case 'ps':
            return ['ps', 'pdf']
        case 'pdf':
            return ['pdf']
        case 'html':
            return ['html']
        case 'pdftex':
            return ['pdf']
        case 'docx':
            return ['pdf', 'docx']
        case 'odf':
            return ['pdf', 'odf']
        case None | '' | 'tex':  # default is tex
            return ['dvi', 'ps', 'pdf']
        case _:  # unexpected
            raise RuntimeError(f"Unexpected source_format {src_fmt}")


def has_ancillary_files(source_flag: str) -> bool:
    """Check source type for indication of ancillary files."""
    if not source_flag:
        return False
    return re.search('A', source_flag, re.IGNORECASE) is not None


def list_ancillary_files(tarball: Optional[FileObj]) -> List[Dict]:
    """Return a list of ancillary files in a tarball (.tar.gz file)."""
    if not tarball or not tarball.name.endswith('.tar.gz') or not tarball.exists():
        return []

    anc_files = []
    try:
        with tarball.open(mode='rb') as fh:
            tf = tarfile.open(fileobj=fh, mode='r')  # type: ignore
            for member in \
                    (m for m in tf if re.search(r'^anc/', m.name) and m.isfile()):
                name = re.sub(r'^anc/', '', member.name)
                size_bytes = member.size
                anc_files.append({'name': name, 'size_bytes': size_bytes})
    except (ReadError, CompressionError) as ex:
        raise Exception(f"Problem while working with tar {tarball}") from ex

    return sorted(anc_files, key=itemgetter('name'))
