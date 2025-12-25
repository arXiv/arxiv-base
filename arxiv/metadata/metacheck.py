import re

from typing import Dict
from typing import Optional
from typing import Tuple

from collections import defaultdict

import gcld3

from arxiv.authors import parse_author_affil

from arxiv.metadata import FieldName
from arxiv.metadata import Disposition
from arxiv.metadata import Complaint
from arxiv.metadata.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS

############################################################
TITLE = FieldName.TITLE
AUTHORS = FieldName.AUTHORS
ABSTRACT = FieldName.ABSTRACT
COMMENTS = FieldName.COMMENTS
REPORT_NUM = FieldName.REPORT_NUM
JOURNAL_REF = FieldName.JOURNAL_REF
DOI = FieldName.DOI
MSC_CLASS = FieldName.MSC_CLASS

OK = Disposition.OK
WARN = Disposition.WARN
HOLD = Disposition.HOLD

CANNOT_BE_EMPTY = Complaint.CANNOT_BE_EMPTY
TOO_SHORT = Complaint.TOO_SHORT
CONTAINS_BAD_STRING = Complaint.CONTAINS_BAD_STRING
EXCESSIVE_CAPITALIZATION = Complaint.EXCESSIVE_CAPITALIZATION
UNBALANCED_BRACKETS = Complaint.UNBALANCED_BRACKETS
BAD_UNICODE = Complaint.BAD_UNICODE
CONTAINS_LONE_SURNAME = Complaint.CONTAINS_LONE_SURNAME
CONTAINS_INITIALS = Complaint.CONTAINS_INITIALS
NO_CAPS_IN_NAME = Complaint.NO_CAPS_IN_NAME
MUST_CONTAIN_LETTERS = Complaint.MUST_CONTAIN_LETTERS
MUST_CONTAIN_DIGITS = Complaint.MUST_CONTAIN_DIGITS
MUST_CONTAIN_YEAR = Complaint.MUST_CONTAIN_YEAR
MUST_BE_ENGLISH = Complaint.MUST_BE_ENGLISH


def complaint2str(complaint: Complaint) -> str:
    if complaint == CANNOT_BE_EMPTY:
        return "Cannot be empty"
    elif complaint == TOO_SHORT:
        return "Too short"
    elif complaint == CONTAINS_BAD_STRING:
        return "Contains bad string"
    elif complaint == EXCESSIVE_CAPITALIZATION:
        return "Excessive capitalization"
    elif complaint == UNBALANCED_BRACKETS:
        return "Unbalanced brackets"
    elif complaint == BAD_UNICODE:
        return "Bad Unicode"
    elif complaint == CONTAINS_LONE_SURNAME:
        return "Contains lone surname"
    elif complaint == CONTAINS_INITIALS:
        return "Name contains initials"
    elif complaint == NO_CAPS_IN_NAME:
        return "No_caps_in_name"
    elif complaint == Complaint.MUST_CONTAIN_LETTERS:
        return "Must contain some letters"
    elif complaint == MUST_CONTAIN_DIGITS:
        return "Must contain some digits"
    elif complaint == Complaint.MUST_CONTAIN_YEAR:
        return "Must contain a year"
    elif complaint == MUST_BE_ENGLISH:
        return "Must be English"
    else:
        return "(Unknown issue)"


def complaint2disposition(complaint: Complaint) -> Disposition:
    if complaint == CANNOT_BE_EMPTY:
        return HOLD
    elif complaint == MUST_CONTAIN_LETTERS:
        return HOLD
    elif complaint == MUST_CONTAIN_DIGITS:
        return HOLD
    else:
        return WARN


############################################################
# Some constants

MIN_TITLE_LEN = 5
MIN_AUTHORS_LEN = 4  # C LI is possible but not C L ?
MIN_ABSTRACT_LEN = 5
# No MIN_COMMENTS_LEN
MIN_REPORT_NUM_LEN = 4
MIN_JOURNAL_REF_LEN = 5
MIN_DOI_LEN = 10  # such as: 10.1234/5678
# No MIN_MSC_CLASS_LEN

MAX_TITLE_LEN = 2000
# No MAX_AUTHORS_LEN?
MAX_ABSTRACT_LEN = 2000
# No MIN_COMMENTS_LEN
MAX_REPORT_NUM_LEN = 2000
MAX_JOURNAL_REF_LEN = 2000
MAX_DOI_LEN = 2000  # such as: 10.1234/5678
# No MAX_MSC_CLASS_LEN

# Language identification is pretty fragile, particularly on short abstracts.
MIN_CHARS_FOR_LID = 20

############################################################


def combine_dispositions(d1: Disposition, d2: Disposition) -> Disposition:
    if d1 == HOLD or d2 == HOLD:
        return HOLD
    elif d1 == WARN or d2 == WARN:
        return WARN
    else:
        return OK


def contains_outside_math(s1: str, s2: str) -> bool:
    """Looks for s1, outside of TeX math
    Not perfect: fails to find xyzzy in $math$ xyzzy $$more math$$.
    """
    if re.search(s1, s2, re.IGNORECASE) and not re.search(
        "[$].*" + s1 + ".*[$]", s2, re.IGNORECASE
    ):
        return True
    else:
        return False


############################################################

# UTF-8 encoding for non-ASCII characters involves a lead byte plus
# 1-3 additional bytes. See https://en.wikipedia.org/wiki/UTF-8
# The first byte is one of:
# 110xxxyy (signalling 2 bytes)
# 1110wwww (signalling 3 bytes)
# or 11110uvv (signalling 4 bytes)
# and the following bytes are 10yyzzzz

# We "detect" UTF-8 which has been decoded (e.g. as Latin-1)
# by looking for two high-bit bytes which match this pattern
# NOTE that this may incorrectly match some real Unicode.

utf8_in_latin1_re = re.compile("[\u00a0-\u00df][\u0080-\u00bf]+")


def contains_utf8_in_latin1(s: str) -> Optional[str]:
    match = utf8_in_latin1_re.search(s)
    if match:
        return match.group(0)
    else:
        return None


# \p{C} would require the regex (not re) module.
# control_chars_re = re.compile("\p{C}+") # looking for "Unicode control characters"
# Looking just for control characters < 32 decimal:
control_chars_re = re.compile("[\u0000-\u001f]+")


def contains_control_characters(s: str) -> Optional[str]:
    match = control_chars_re.search(s)
    if match:
        return match.group(0)
    else:
        return None

# Allow newlines (\n = u\000a) in abstracts
control_chars_for_abs_re = re.compile("[\u0000-\u0009\u000b-\u001f]+")

def contains_control_characters_for_abs(s: str) -> Optional[str]:
    match = control_chars_for_abs_re.search(s)
    if match:
        return match.group(0)
    else:
        return None
    

############################################################
# Check report objects are a string (disposition)
# and a list of complaints
# Each complaint is a string and a list of contexts.


class MetadataCheckReport:
    def __init__(self):
        self.disposition: Disposition = OK
        self.complaints = set()
        # map from complaint to offsets, if available
        self.offsets: Dict[Complaint, list[Tuple[int,int]]] = defaultdict(list)

    def __repr__(self):
        if self.disposition == OK:
            return f"<MetadataCheckReport OK>"
        else:
            return f"<MetadataCheckReport {self.disposition}: {self.get_offsets()}>"

    def add_complaint(self, complaint: Complaint, offsets: Optional[Tuple[int,int]] = None):
        disposition = complaint2disposition(complaint)
        self.disposition = combine_dispositions(self.disposition, disposition)
        self.complaints.add(complaint)
        if offsets:
            self.offsets[complaint].append(offsets)

    def get_disposition(self) -> Disposition:
        return self.disposition

    def get_offsets(self):
        return self.offsets     # ???
    
    def get_complaints(self):
        return self.complaints


############################################################

# This is the main function

from typing import TypedDict
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class MetadataProtocol(Protocol):
    title: str
    authors: str
    abstract: str
    comments: str
    report_num: str
    journal_ref: str
    doi: str
    msc_class: str
    acm_class: str

@dataclass
class Metadata:      # implements MetadataProtocol
    title: str
    authors: str
    abstract: str
    comments: str
    report_num: str
    journal_ref: str
    doi: str
    msc_class: str
    acm_class: str
    
    def __init__(self):
        self.title = None
        self.authors = None        
        self.abstract = None        
        self.comments = None        
        self.report_num = None        
        self.journal_ref = None
        self.doi = None
        self.msc_class = None
        self.acm_class = None        
        pass

############################################################    
# def check(metadata: Dict[FieldName, str]) -> Dict[FieldName, MetadataCheckReport]:
def check(metadata: MetadataProtocol) -> Dict[FieldName, MetadataCheckReport]:
    result = {}
    if metadata.title is not None:
        result[TITLE] = check_title(metadata.title)
    if metadata.authors is not None:
        result[AUTHORS] = check_authors(metadata.authors)
    if metadata.abstract is not None:
        result[ABSTRACT] = check_abstract(metadata.abstract)
    if metadata.comments is not None:
        result[COMMENTS] = check_comments(metadata.comments)
    if metadata.report_num is not None:
        result[REPORT_NUM] = check_report_num(metadata.report_num)
    if metadata.journal_ref is not None:
        result[JOURNAL_REF] = check_journal_ref(metadata.journal_ref)
    if metadata.doi is not None:
        result[DOI] = check_doi(metadata.doi)
    if metadata.msc_class is not None:
        result[MSC_CLASS] = check_msc_class(metadata.msc_class)
    # TODO: acm_class?
    return result


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


############################################################


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


############################################################


def starts_with_lowercase(s: str) -> bool:
    """
    Detect titles which start with a lower case char, eg "bad title"
    Do nothing smart with "k-means", "eSpeak", or "tugEMM".
    """

    if len(s) < 1:
        return False
    if re.match("[a-z]", s):
        return True
    else:
        return False
    #


############################################################


def all_brackets_balanced(s: str) -> bool:
    pending_brackets = []
    for c in s:
        if c == "(":
            pending_brackets.append(")")
        elif c == "[":
            pending_brackets.append("]")
        elif c == "{":
            pending_brackets.append("}")
        elif len(pending_brackets) > 0 and c == pending_brackets[-1]:
            pending_brackets = pending_brackets[:-1]
        elif c in ")}]":
            return False
    #
    return len(pending_brackets) == 0

# assert( all_brackets_balanced( "(())[({})] [] {}" ) )
# assert( not all_brackets_balanced( "test ] test" ) )


def language_is_not_english(s: str) -> bool:
    """
    use gcld3 to detect the "primary" language (abstract only)

    return True only if the primary language appears to be
    something other than English.
    """
    if len(s) < MIN_CHARS_FOR_LID:
        return False  #
    # Not very reliable with < 50 chars...
    lid = gcld3.NNetLanguageIdentifier(MIN_CHARS_FOR_LID, 1000)  # min, max num bytes
    result = lid.FindLanguage(s)
    if result.is_reliable and result.language != "en":
        return True
    else:
        return False


############################################################

HTML_ELEMENTS = [
    "<p[^a-z]",
    "</p><div[^a-z]",
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


def contains_html_elements(s: str) -> bool:
    """
    Detect common HTML elements:
    <p> <div> <br> <img> <sup> <sub> and <table>

    - but not <a> <b> ... <x> <y> or <z>
    (note that <p> is still banned!)
    """
    for element in HTML_ELEMENTS:
        if re.search(element, s, re.IGNORECASE):
            return True
        #
    #
    return False


# ) must be allowed
# *, #, ^, @ are problematic in authors, and detected elsewhere
ENDS_WITH_PUNCTUATION_RE = re.compile("^.*[!$%^&(_=`:;,.?-]$")


def ends_with_punctuation(s: str) -> bool:
    """
    Detect common punctuation which should not appear at the end of the authors list
    """
    # match = ENDS_WITH_PUNCTUATION_RE.search(s)
    match = ENDS_WITH_PUNCTUATION_RE.match(s)
    if match:
        return match.group(0)
    else:
        return None


def check_bad_whitespace(v: str, report):
    #
    if re.match(r"^\s", v):
        report.add_complaint(CONTAINS_BAD_STRING, "leading whitespace")
    #
    if re.search(r"\s$", v):
        report.add_complaint(CONTAINS_BAD_STRING, "trailing whitespace")
    #
    # Careful: \s matches \n!
    if re.search(r"[ \t][ \t]", v):
        report.add_complaint(CONTAINS_BAD_STRING, "excess whitespace")
    #
    # JHY: these should be "fixable": s/\s*,\s*,\s*/, / and s/\s*,\s*/, / !
    if re.search(r",\s*,", v):
        report.add_complaint(CONTAINS_BAD_STRING, "two adjacent commas")
    elif re.search(r"\s,", v):
        report.add_complaint(CONTAINS_BAD_STRING, "whitespace before comma")
    elif re.search(r",[a-zA-Z]", v):
        report.add_complaint(CONTAINS_BAD_STRING, "no whitespace after comma")
    #
    if re.match(r"[^\s]\(", v):
        report.add_complaint(CONTAINS_BAD_STRING, "no space before open paren")
    #
    if re.match(r"\(\s", v):
        report.add_complaint(CONTAINS_BAD_STRING, "space after open paren")
    #
    if re.match(r"\s\)", v):
        report.add_complaint(CONTAINS_BAD_STRING, "space before close paren")
    #
    if re.match(r"\)[^\s]", v):
        report.add_complaint(CONTAINS_BAD_STRING, "no space after close paren")
    #
    


############################################################


def check_title(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint(CANNOT_BE_EMPTY)
    elif len(v) < MIN_TITLE_LEN:
        report.add_complaint(TOO_SHORT)
        print( "jjj: TITLE TOO SHORT", report.get_complaints() )
    elif len(v) > MAX_TITLE_LEN:
        report.add_complaint(TOO_LONG)
    else:
        print( "jjj: TITLE NOT TOO SHORT NOR LONG" )
    #
    if re.match(r"title\b", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "title")
    #
    # TODO: leading, trailing, excess space?
    if re.search(r"\\\\", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\\\ (line break)")
    #
    if looks_like_all_caps(v):
        report.add_complaint(CONTAINS_BAD_STRING, "excessive capitalization")
    elif long_word_caps(v):
        report.add_complaint(CONTAINS_BAD_STRING, "excessive capitalization")
    #
    if starts_with_lowercase(v):
        report.add_complaint(CONTAINS_BAD_STRING, v[0])
    #
    if re.search(r"\\href{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\href")
    #
    if re.search(r"\\url{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\url")
    #
    if contains_outside_math(r"\\emph", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\emph")
    #
    if contains_outside_math(r"\\uline", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\uline")
    #
    if contains_outside_math(r"\\textbf", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textbf")
    #
    if contains_outside_math(r"\\texttt", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\texttt")
    #
    if contains_outside_math(r"\\textsc", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textsc")
    #
    if contains_outside_math(r"\\#", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\#")
    #
    if contains_outside_math(r"\\%", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\%")
    #
    check_bad_whitespace(v, report)
    #
    if contains_html_elements(v):
        report.add_complaint(CONTAINS_BAD_STRING, "HTML")
    #
    if not all_brackets_balanced(v):
        report.add_complaint(UNBALANCED_BRACKETS)
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #
    # not implemented: titles MAY end with punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report


def check_authors(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # (Field must not be blank)
    if len(v) < MIN_AUTHORS_LEN:
        report.add_complaint(TOO_SHORT)
    # NO max authors len!
    # elif len(v) > MAX_AUTHORS_LEN:
    #     report.add_complaint(TOO_LONG)
    #
    if re.search(r"\\\\", v):
        report.add_complaint(CONTAINS_BAD_STRING, "line break (\\\\)")
    #
    if re.search(r"\*", v):
        report.add_complaint(CONTAINS_BAD_STRING, "bad character '*'")
    #
    if re.search(r"#", v):
        report.add_complaint(CONTAINS_BAD_STRING, "bad character '#'")
    #
    if re.search(r"[^\\]\^", v):
        report.add_complaint(CONTAINS_BAD_STRING, "bad character '^'")
    #
    if re.search(r"@", v):
        report.add_complaint(CONTAINS_BAD_STRING, "bad character '@'")
    #
    check_bad_whitespace(v, report)
    #
    if re.search(r"anonym", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "anonymous")
    #
    if re.search(r"corresponding", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "'corresponding'")
    #
    for s in ("\\dag", "\\ddag", "\\textdag", "\\textddag"):
        if re.match(s, v, re.IGNORECASE):
            report.add_complaint(CONTAINS_BAD_STRING, f"dagger symbol {s}")
            break
        #
    #
    if re.match(r"authors\b", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "authors")
    elif re.match(r"author\b", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "author")
    #
    if contains_html_elements(v):
        report.add_complaint(CONTAINS_BAD_STRING, "HTML")
    #
    print( "CHECKING BREACKETS" )
    if not all_brackets_balanced(v):
        report.add_complaint(UNBALANCED_BRACKETS)
    #
    if re.search(r"\( ", v):
        report.add_complaint(
            CONTAINS_BAD_STRING, "space after open paren"
        )
    if re.search(r" \)", v):
        report.add_complaint(
            CONTAINS_BAD_STRING, "space before close paren"
        )
    # Do I need to parse the authors list first?
    if re.search(r";", v) and not re.search("(.*;.*)", v):
        report.add_complaint(
            CONTAINS_BAD_STRING, "use commas, not ';' to separate authors"
        )
    # Are tildes allowed anywhere? Yes, as a TeX accent
    # (Consider: only check names?)
    if re.search(r"[^\\]~", v):
        report.add_complaint(
            CONTAINS_BAD_STRING, "~ (tilde)"
        )
    #
    # Authors list can NOT end with punctuation
    if s := ends_with_punctuation(v):
        if not v.endswith("et al."):
            report.add_complaint(CONTAINS_BAD_STRING, s)
        #
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #

    # Parse authors, check authors names - but not affiliations - for:
    # ALL CAPS (disabled?)
    # single word in all CAPS (also disabled)
    # [...] (in author name)
    # Numbers (but Jennifer 8 Lee!)
    # IEEE (confusable with affiliation)
    # phd, prof, dr
    # Single initial after parsing authors (disabled)
    # TODO: letters after name (BUT Indian names like RS, etc?)
    # TODO: extra curlies in TeX accents, e.g.: {\'e}
    # (TODO: allow all Unicode ?)
    # TODO: urls

    # TODO: maybe remove duplicates from the complaints list

    parsed_authors = parse_author_affil(v)  # => List[List[str]]
    for author in parsed_authors:
        # first is "keyname" (surname?), second is fist name(s), third is suffix
        keyname = author[0]
        firstname = author[1]
        suffix = author[2]

        check_one_author(report, keyname, firstname, suffix)  # updates report
    # end for author in parsed_authors

    return report


def check_one_author(report, keyname, firstname, suffix) -> None:
    # report may be side-effected

    # Some quick special cases to skip:
    if keyname.lower() == "author" and firstname == "" and suffix == "":
        return
    if keyname.lower() == "authors" and firstname == "" and suffix == "":
        return
    if keyname == ":" and firstname == "" and suffix == "":
        return
    #
    if suffix:
        if firstname:
            name = f"{firstname} {keyname} {suffix}"
        else:
            name = f"{keyname} {suffix}"  # ???
        #
    elif firstname:
        name = f"{firstname} {keyname}"
    else:
        name = keyname
    #
    if firstname == "":
        if (
            re.search(r"collaboration", name, re.IGNORECASE)
            or re.search(r"collaborative", name, re.IGNORECASE)
            or re.search(r"project", name, re.IGNORECASE)
            or re.search(r"group", name, re.IGNORECASE)
            or re.search(r"team", name, re.IGNORECASE)
            or re.search(r"belle", name, re.IGNORECASE)
        ):
            pass
        else:
            report.add_complaint(CONTAINS_LONE_SURNAME, f"'{name}'")
        #
    #
    # Don't reject Sylvie ROUX nor S ROUX
    if re.match("^[A-Z]{3,}$", keyname) and re.match("^[A-Z]{3,}$", firstname):
        report.add_complaint(EXCESSIVE_CAPITALIZATION, f"'{name}'")
    #
    # Allow "Chandrasekar R" but not "Chandra R."
    if re.match(r"^[A-Z]\.$", keyname):
        report.add_complaint(CONTAINS_INITIALS, f"'{name}'")
    elif keyname and re.match(r"\.$", keyname):
        report.add_complaint(CONTAINS_BAD_STRING, f"final '.'")
    elif (not keyname) and re.match(r"\.$", surname):
        report.add_complaint(CONTAINS_BAD_STRING, f"final '.'")
    #
    # Reject e. e. cummings and "evans". Don't reject J von
    if keyname == keyname.lower() and (
        firstname is None or firstname == firstname.lower()
    ):
        report.add_complaint(NO_CAPS_IN_NAME, f"'{name}'")
    #
    if (
        re.search(r"\[|]", keyname)
        or re.search(r"\[|]", firstname)
        or re.search(r"\[|]", suffix)
    ):
        report.add_complaint(CONTAINS_BAD_STRING, f"'|' in '{name}'")
    #
    if (
        re.search("[0-9]", keyname)
        or re.search("[0-9]", firstname)
        or re.search("[0-9]", suffix)
    ):
        report.add_complaint(CONTAINS_BAD_STRING, f"Digits in '{name}'")
    #
    # match A. and A.B. but not IV or other roman numerals
    if (
        re.match(r"^[A-Z]\.$", suffix)
        or re.match(r"^[A-Z]\.[A-Z]\.$", suffix)
        or re.match(r"^[A-Z]\.[A-Z]\.[A-Z]\.$", suffix)
    ):
        report.add_complaint(CONTAINS_INITIALS, f"Initials in '{name}'")
    #
    for badmessage, badpattern in (
        (";", ";"),
        ("IEEE", r"\bIEEE\b"),
        ("PhD", r"\bphd\b"),
        ("prof", r"\bprof\b"),
        ("dr", r"\bdr\b"),
        ("Physics", r"\bPhysics\b"),
        ("Math", r"\bMath\b"),  # BUT watch out for Math\'eo ?
        ("Inst", r"\bInst\b"),
        ("Institute", r"\bInstitute\b"),
        ("Dept", r"\bDept\b"),
        ("Department", r"\bDepartment\b"),
        ("Univ", r"\bUniv\b"),
        ("University", r"\bUniversity\b"),
        ("chatgpt", r"\bchatgpt?\b"),
        ("GPT-3.5", r"\bGPT-3.5\b"),
        ("GPT-4", r"\bGPT-4"),  # Also match 4o, etc
        ("PaLM2", r"\bPalM2\b"),
        # Claude and Bert are too common
    ):
        if (
            re.search(badpattern, keyname, re.IGNORECASE)
            or re.search(badpattern, firstname, re.IGNORECASE)
            or re.search(badpattern, suffix, re.IGNORECASE)
        ):
            # print( keyname, firstname, suffix )
            report.add_complaint(CONTAINS_BAD_STRING, f"{badmessage} in '{name}'")
        #
    # end for badword in badwords

    for badword in ("Llama", "Olamma", "Gemini", "Claude", "Bert", "Bart"):
        if badword.lower() == keyname.lower() and firstname == "" and suffix == "":
            report.add_complaint(CONTAINS_BAD_STRING, f"'{badword}'")
        #
    #


def check_abstract(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint(CANNOT_BE_EMPTY)
    elif len(v) < MIN_ABSTRACT_LEN:
        report.add_complaint(TOO_SHORT)
    elif len(v) > MAX_ABSTRACT_LEN:
        report.add_complaint(TOO_LONG)
    #
    # Only match beginning!
    if re.match(r"abstract\b", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "abstract")
    #
    # ARXIVCE-812
    # Don't warn about "\\" in abstracts - too common (about 50/month)
    # Don't complain about "\n"
    # Also, don't complain about "\n  " (paragraph break!
    # if re.search("\n", "".join(v.split("\n  "))):
    #     report.add_complaint(CONTAINS_BAD_STRING, "\\n (line break)")
    # 
    # QA-70 do warn about paragraphs which end in newlines
    # " \n" or "\n\s+\n".
    # But allow \n\n (and \n-----\n)"
    if (
        re.search(r"\s+\n", v) # includes \n\s+\n
        # or re.search(r"\s+$", v) # covered above
    ):
        report.add_complaint(CONTAINS_BAD_STRING, "whitespace at end of paragraph")
    #
    if looks_like_all_caps(v):
        report.add_complaint(CONTAINS_BAD_STRING, "(capitalization)")
    #
    if starts_with_lowercase(v):
        report.add_complaint(
            CONTAINS_BAD_STRING, f"starts with a lower case letter ({v[0]})"
        )
    #
    if re.search(r"\\href{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\href")
    #
    if re.search(r"\\url{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\url")
    #
    if contains_outside_math(r"\\emph", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\emph")
    #
    if contains_outside_math(r"\\uline", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\uline")
    #
    if contains_outside_math(r"\\textbf", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textbf")
    #
    if contains_outside_math(r"\\texttt", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\texttt")
    #
    if contains_outside_math(r"\\textsc", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textsc")
    #
    if contains_outside_math(r"\\#", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\#")
    #
    if contains_outside_math(r"\\%", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\%")
    #
    check_bad_whitespace(v, report)
    #
    if contains_html_elements(v):
        report.add_complaint(CONTAINS_BAD_STRING, "(HTML)")
    #
    if not all_brackets_balanced(v):
        report.add_complaint(UNBALANCED_BRACKETS)
    #
    # JHY: \begin{equation}, etc are permitted ...
    if re.search(r"\\begin[^{]", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\begin")
    #
    if language_is_not_english(v):
        report.add_complaint(MUST_BE_ENGLISH)
    #
    if s := contains_control_characters_for_abs(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #
    # not implemented: abstract MAY end in punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report


def check_comments(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # Empty comments are ok!
    if re.search(r"\\\\", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\\\ (TeX line break) ")
    #
    if looks_like_all_caps(v):
        report.add_complaint(CONTAINS_BAD_STRING, v)
    #
    if re.search(r"\\href{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\href")
    #
    if re.search(r"\\url{", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\url")
    #
    if contains_outside_math(r"\\emph", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\emph")
    #
    if contains_outside_math(r"\\uline", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\uline")
    #
    if contains_outside_math(r"\\textbf", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textbf")
    #
    if contains_outside_math(r"\\texttt", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\texttt")
    #
    if contains_outside_math(r"\\textsc", v):
        report.add_complaint(CONTAINS_BAD_STRING, "\\textsc")
    #
    if contains_outside_math(r"\\#", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\#")
    #
    if contains_outside_math(r"\\%", v):
        report.add_complaint(CONTAINS_BAD_STRING, "unnecessary escape: \\%")
    #
    check_bad_whitespace(v, report)
    #
    if not all_brackets_balanced(v):
        report.add_complaint(UNBALANCED_BRACKETS)
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #
    # TODO: check that language is English?

    return report


def check_report_num(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_REPORT_NUM_LEN:
        report.add_complaint(TOO_SHORT)
        return report
    elif len(v) > MAX_REPORT_NUM_LEN:
        report.add_complaint(TOO_LONG)
    #
    if re.match(r"^[0-9]*$", v):
        report.add_complaint(MUST_CONTAIN_LETTERS)
    if re.match(r"^[A-Za-z-]*$", v):
        report.add_complaint(MUST_CONTAIN_DIGITS)
    # TODO: URLs?
    #
    check_bad_whitespace(v, report)
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    return report


def check_journal_ref(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_JOURNAL_REF_LEN:
        report.add_complaint(TOO_SHORT)
    elif len(v) > MAX_JOURNAL_REF_LEN:
        report.add_complaint(TOO_LONG)
    #
    # TODO: check for author name(s) in jref
    # TODO: check for paper title in jref
    if re.search("http:", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "http:")
    elif re.search("https:", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "https:")
    #
    if re.search("doi", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "DOI")
    #
    if re.search("accepted", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "accepted")
    #
    if re.search("submitted", v, re.IGNORECASE):
        report.add_complaint(CONTAINS_BAD_STRING, "submitted")
    #
    check_bad_whitespace(v, report)
    #
    # Removed Oct 2025
    # if not re.search("[12][90][0-9][0-9]", v):
    #     report.add_complaint(MUST_CONTAIN_YEAR)
    #
    for s in ("title", "booktitle", "inproceedings"):
        if re.search(f"{s}=", v, re.IGNORECASE):
            report.add_complaint(CONTAINS_BAD_STRING, f"{s} (bibtex?)")
            break
        #
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    # Hopefully, this is "validate input encoding"
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #
    return report


def check_doi(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_DOI_LEN:
        print( "DOI TOO SHORT ???" )
        report.add_complaint(TOO_SHORT)
    elif len(v) > MAX_DOI_LEN:
        report.add_complaint(TOO_LONG)
    #
    # if re.search("http:", v):
    #     report.add_complaint(CONTAINS_BAD_STRING, "http:")
    # if re.search("https:", v):
    #     report.add_complaint(CONTAINS_BAD_STRING, "https:")
    # TODO: should we look for "doi:"?
    # if re.search("arxiv-doi", v):
    #     report.add_complaint(CONTAINS_BAD_STRING, "arxiv-doi")
    #
    print( "DOI: check whitespace ???" )

    check_bad_whitespace(v, report)

    
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    # Hopefully, this is "validate input encoding"
    # if s := contains_utf8_in_latin1(v):
    #     report.add_complaint(BAD_UNICODE, s)
    #
    # Consider separating this out?
    for doi in v.split():
        if not re.match("^[0-9][0-9]*.[0-9][0-9]*/[A-Za-z0-9():;._/-]*$", doi):
            report.add_complaint(CONTAINS_BAD_STRING, v)
        #
    #
    print( "REPORT", report.offsets )
           
    return report


def check_msc_class(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if re.search("http:", v):
        report.add_complaint(CONTAINS_BAD_STRING, "http:")
    if re.search("https:", v):
        report.add_complaint(CONTAINS_BAD_STRING, "https:")
    # TODO: should we look for "doi:"?
    if re.search("arxiv-doi", v):
        report.add_complaint(CONTAINS_BAD_STRING, "arxiv-doi")
    #
    check_bad_whitespace(v, report)
    #
    if s := contains_control_characters(v):
        report.add_complaint(CONTAINS_BAD_STRING, repr(s))
    #
    if s := contains_utf8_in_latin1(v):
        report.add_complaint(BAD_UNICODE, s)
    #
    if re.search(r";", v):
        report.add_complaint(
            CONTAINS_BAD_STRING, "use commas, not ';' to separate MSC classes"
        )
    #
    # TODO: don't show these to editors?
    # for s in ("MSC *class", "MSC number"):
    #     if re.search(f"{s}=", v, re.IGNORECASE):
    #         report.add_complaint(CONTAINS_BAD_STRING, s)
    #         break
    #     #
    # #

    print( "REPORT", report.offsets )
           
    return report


# Is minlen <= 4 for authors field too strict?
#
# Check for \n but not \n<space><space> (a paragraph break) in abstract?
# Note: no checks for other fields.

