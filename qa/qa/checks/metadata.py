import re
from pydantic import BaseModel
from typing import Optional

from qa.checks.base import BaseCheck
from qa.checks import models

# TODO remove
from arxiv.metadata import Disposition, Complaint
from arxiv.metadata.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS


control_chars_re = r"[\u0000-\u001f]+"
utf8_in_latin1_re = r"[\u00c0-\u00ff][\u0080-\u00bf]+"

MIN_TITLE_LEN = 5
MAX_TITLE_LEN = 2000
HTML_ELEMENTS = [
    # "<p[^a-z]",
    "<p>",
    "<p ",
    "</p>",
    "<div[^a-z]",
    "</div>",
    "<br[^a-z]",
    "</br>",
    # Allow <a>
    "</a>",
    "<img[^a-z]",
    "</img>",
    "<sup[^a-z]",
    "</sup>",
    "<sub[^a-z]",
    "</sub>",
    "<table[^a-z]",
    "</table>",
]


def complaint2disposition(complaint: Complaint) -> Disposition:
    if complaint == Complaint.CANNOT_BE_EMPTY:
        return Disposition.HOLD
    elif complaint == Complaint.MUST_CONTAIN_LETTERS:
        return Disposition.HOLD
    elif complaint == Complaint.MUST_CONTAIN_DIGITS:
        return Disposition.HOLD
    else:
        return Disposition.WARN


def combine_dispositions(d1: Disposition, d2: Disposition) -> Disposition:
    if d1 == Disposition.HOLD or d2 == Disposition.HOLD:
        return Disposition.HOLD
    elif d1 == Disposition.WARN or d2 == Disposition.WARN:
        return Disposition.WARN
    else:
        return Disposition.OK


class MetadataCheckReport(BaseModel):
    disposition: Disposition = Disposition.OK
    complaints: set[Complaint] = set()
    offsets: dict[Complaint, list[tuple[int, int]]] = dict(list)  # defaultdict?

    def __repr__(self):
        if self.disposition == Disposition.OK:
            return f"<MetadataCheckReport OK>"
        else:
            return f"<MetadataCheckReport {self.disposition}: {self.get_offsets()}>"

    def add_complaint(
        self, complaint: Complaint, offsets: Optional[tuple[int, int]] = None
    ):
        disposition = complaint2disposition(complaint)
        self.disposition = combine_dispositions(self.disposition, disposition)
        self.complaints.add(complaint)
        if offsets:
            self.offsets[complaint].append(offsets)


def add_complaints_matching(
    regex: str, v: str, complaint: Complaint, report: MetadataCheckReport
):
    # Do not ignore case here, do it inside the regex
    for m in re.finditer(regex, v):
        report.add_complaint(complaint, (m.start(), m.end()))


def check_starts_with_lowercase(v: str, report: MetadataCheckReport):
    """
    Detect fields (especially titles) which start with a lower case char, eg "bad title"
    TODO: Do nothing smart with "k-means", "eSpeak", or "tugEMM".
    """
    # Don't use add_complaints_matching - it is case-insensitive!
    if re.match(r"^[a-z]", v):
        report.add_complaint(Complaint.BEGINS_WITH_LOWERCASE, (0, 1))
    #


def looks_like_all_caps(s: str) -> bool:
    """
    Returns true if s appears to have all/excessive capitals. The
    exact threshold is heuristic based on looking at submissions over
    March 2010.
    """
    num_caps = sum([c.isupper() for c in s])
    num_lower = sum([c.islower() for c in s])
    if num_caps > num_lower * 2 + 7:
        return True
    else:
        return False


def long_word_caps(s: str) -> bool:
    """
    Returns true (was: a list of long words) if s appears to have
    two or more words which are
    * at least 6 characters long,
    * in all caps (possibly including internal hyphens),
    * and which are not in our list of KNOWN_WORDS_IN_ALL_CAPS.
    """
    num_matches = 0
    for word in s.split():
        if (
            len(word) >= 6
            and re.match("^[A-Z][A-Z-]*[A-Z]$", word)
            and word not in KNOWN_WORDS_IN_ALL_CAPS
        ):
            num_matches += 1
        #
    #
    return num_matches > 1


def check_bad_whitespace(v: str, report: MetadataCheckReport, for_abs: bool = False):
    #
    add_complaints_matching(r"^\s", v, Complaint.LEADING_WHITESPACE, report)
    add_complaints_matching(r"\s$", v, Complaint.TRAILING_WHITESPACE, report)
    # Fixable!
    # Careful: \s matches \n!
    # Careful: [ \t][ \t] matches beginning and end of strings, too!
    # Careful: now it's matching the surrounding chars, too!
    if for_abs:
        # space followed by newline is still a problem
        add_complaints_matching(r"\s+\n", v, Complaint.EXTRA_WHITESPACE_ABS, report)
        # \n \n should not be detected here !?
        add_complaints_matching(
            r"[^ \t\n,][ \t][ \t]+[^ \t\n,]", v, Complaint.EXTRA_WHITESPACE, report
        )
    else:
        add_complaints_matching(
            r"[^ \t,][ \t][ \t]+[^ \t,]", v, Complaint.EXTRA_WHITESPACE, report
        )
    #
    # Problems: space comma; comma (spaces) comma;
    # DO NOT fix "comma alpha" (e.g. f(a,b) !)
    # JHY: these should be "fixable": s/\s*,\s*,\s*/, / and s/\s*,\s*/, / !
    # add_complaints_matching(r"(?i)\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+[a-zA-Z]?|\s*,(\s*,)+", v, Complaint.EXTRA_WHITESPACE, report)
    add_complaints_matching(
        r"(?i)\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+", v, Complaint.EXTRA_WHITESPACE, report
    )

    # Careful: parens can be preceded by letters
    # also, parens can be followed by whitespace or punctuation
    # Stop complaining about "O(n)" and "sin(x)"!
    # add_complaints_matching(r"(?i)[a-zA-Z]\(", v, Complaint.BAD_CHARACTER, report)
    # Also letters, e.g. H2SO4
    # e.g. Ca10(PO4)6(OH)2 – Hydroxyapatite
    # add_complaints_matching(r"(?i)\)[a-zA-Z]", v, Complaint.BAD_CHARACTER, report)

    add_complaints_matching(
        r"(?i)\(\s", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report
    )
    add_complaints_matching(
        r"(?i)\s\)", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report
    )


def check_html_elements(v: str, report: MetadataCheckReport):
    """
    Detect common HTML elements:
    <p> <div> <br> <img> <sup> <sub> and <table>

    - but not <a> <b> ... <x> <y> or <z>
    (note that <p> is still banned!)
    """
    for element in HTML_ELEMENTS:
        add_complaints_matching(element, v, Complaint.CONTAINS_HTML, report)
    #


def all_brackets_balanced(s: str) -> bool:
    pending_brackets = []
    for c in s:
        if c == "(":
            pending_brackets.append(")")
        elif c == "[":
            pending_brackets.append("]")
        elif c == "{":
            pending_brackets.append("}")
        elif len(pending_brackets) > 0 and (
            c == pending_brackets[-1]
            or (c == ")" and pending_brackets[-1] == "]")
            or (c == "]" and pending_brackets[-1] == ")")
        ):
            # Pop one
            pending_brackets = pending_brackets[:-1]
        elif c in ")}]":
            return False
    #
    return len(pending_brackets) == 0


class TitleCheck(BaseCheck):
    name = "title_check"
    version = "1.0"
    description = "Aggregated metadata checks for title field."

    required_data = {"metadata"}
    results_model = MetadataCheckReport

    def _run(self, data: models.CheckData) -> models.CheckResult:
        report = MetadataCheckReport()

        title = data.metadata.title

        # check length
        if title is None or title == "":
            report.add_complaint(Complaint.CANNOT_BE_EMPTY)
        elif len(title) < MIN_TITLE_LEN:
            report.add_complaint(Complaint.TOO_SHORT)
        elif len(title) > MAX_TITLE_LEN:
            report.add_complaint(Complaint.TOO_LONG)
        else:
            pass

        add_complaints_matching(
            r"(?i)^title:?\b", title, Complaint.BEGINS_WITH_TITLE, report
        )
        #
        add_complaints_matching(
            r"(?i)\\\\", title, Complaint.CONTAINS_LINEBREAK, report
        )
        #
        if looks_like_all_caps(title):
            report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
        elif long_word_caps(title):
            report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
        #
        check_starts_with_lowercase(title, report)
        #
        add_complaints_matching(r"(?i)\\#", title, Complaint.UNNECESSARY_ESCAPE, report)
        add_complaints_matching(r"(?i)\\%", title, Complaint.UNNECESSARY_ESCAPE, report)
        add_complaints_matching(r"(?i)\\href{", title, Complaint.CONTAINS_TEX, report)
        add_complaints_matching(r"(?i)\\url{", title, Complaint.CONTAINS_TEX, report)
        #
        check_bad_whitespace(title, report)
        #
        check_html_elements(title, report)
        #
        if not all_brackets_balanced(title):
            report.add_complaint(Complaint.UNBALANCED_BRACKETS)
        #
        add_complaints_matching(
            control_chars_re, title, Complaint.CONTAINS_CONTROL_CHARS, report
        )
        add_complaints_matching(
            utf8_in_latin1_re, title, Complaint.BAD_UNICODE_ENCODING, report
        )
        #
        # not implemented: titles MAY end with punctuation
        # not implemented: check for arXiv or arXiv:ID
        return report


# def check_title(v: str) -> MetadataCheckReport:
#     report = MetadataCheckReport()
#     if v is None or v == "":
#         report.add_complaint(Complaint.CANNOT_BE_EMPTY)
#     elif len(v) < MIN_TITLE_LEN:
#         report.add_complaint(Complaint.TOO_SHORT)
#     elif len(v) > MAX_TITLE_LEN:
#         report.add_complaint(Complaint.TOO_LONG)
#     else:
#         pass
#     #
#     add_complaints_matching(r"(?i)^title:?\b", v, Complaint.BEGINS_WITH_TITLE, report)
#     #
#     add_complaints_matching(r"(?i)\\\\", v, Complaint.CONTAINS_LINEBREAK, report)
#     #
#     if looks_like_all_caps(v):
#         report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
#     elif long_word_caps(v):
#         report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
#     #
#     check_starts_with_lowercase(v, report)
#     #
#     add_complaints_matching(r"(?i)\\#", v, Complaint.UNNECESSARY_ESCAPE, report)
#     add_complaints_matching(r"(?i)\\%", v, Complaint.UNNECESSARY_ESCAPE, report)
#     add_complaints_matching(r"(?i)\\href{", v, Complaint.CONTAINS_TEX, report)
#     add_complaints_matching(r"(?i)\\url{", v, Complaint.CONTAINS_TEX, report)
#     #
#     check_bad_whitespace(v, report)
#     #
#     check_html_elements(v, report)
#     #
#     if not all_brackets_balanced(v):
#         report.add_complaint(Complaint.UNBALANCED_BRACKETS)
#     #
#     add_complaints_matching(
#         control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report
#     )
#     add_complaints_matching(
#         utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report
#     )
#     #
#     # not implemented: titles MAY end with punctuation
#     # not implemented: check for arXiv or arXiv:ID
#     return report
