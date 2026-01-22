import re

from typing import (
    Dict,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypedDict,
    runtime_checkable,
)

from dataclasses import dataclass

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

def complaint2str(complaint: Complaint) -> str:
    if complaint == Complaint.CANNOT_BE_EMPTY:
        return "Cannot be empty."
    elif complaint == Complaint.TOO_SHORT:
        return "Text likely too short"
    elif complaint == Complaint.BEGINS_WITH_TITLE:
        return "Begins with 'title'."
    elif complaint == Complaint.BEGINS_WITH_AUTHOR:
        return "Begins with 'author'."
    elif complaint == Complaint.BEGINS_WITH_ABSTRACT:
        return "Begins with 'abstract'."
    elif complaint == Complaint.CONTAINS_LINEBREAK:
        return "Contains a line break."
    elif complaint == Complaint.EXCESSIVE_CAPITALIZATION:
        return "Likely excessive capitalization"
    elif complaint == Complaint.BEGINS_WITH_LOWERCASE:
        return "Begins with a lower case letter."
    elif complaint == Complaint.CONAINS_TEX:
        return "Contains TeX."
    elif complaint == Complaint.UNNECESSARY_ESCAPE:
        return "Contains unnecessary escape."
    elif complaint == Complaint.CONTAINS_HTML:
        return "Contains HTML."
    elif complaint == Complaint.UNBALANCED_BRACKETS:
        return "Unbalanced brackets."
    elif complaint == Complaint.BAD_UNICODE_ENCODING:
        return "Bad Unicode encoding."
    elif complaint == Complaint.BAD_CHARACTER:
        return "Unusual character detected."
    elif complaint == Complaint.LEADING_WHITESPACE:
        return "Leading whitespace."
    elif complaint == Complaint.TRAILING_WHITESPACE:
        return "Trailing whitespace."
    elif complaint == Complaint.WHITESPACE_BEFORE_COMMA:
        return "Whitespace before a comma."
    elif complaint == Complaint.CONTAINS_ANONYMOUS:
        return "Contains anonymous or missing author name." # ???
    elif complaint == Complaint.CONTAINS_CORRESPONDING:
        return "Contains 'corresponding'."
    elif complaint == Complaint.CONTAINS_DAGGER:
        return "Contains a dagger symbol."
    elif complaint == Complaint.CONTAINS_SEMICOLON:
        return "Contains semicolon(s) - use ',' or 'and' to separate authors."
    elif complaint == Complaint.CONTAINS_LONE_SURNAME:
        return "Contains lone surname"
    # elif complaint == Complaint.CONTAINS_INITIALS:
    #     return "Name contains initials"
    elif complaint == Complaint.CONTAINS_AFFILIATION:
        return "Contains a suffix that may be university affiliation or degree related."
    elif complaint == Complaint.EXTRA_WHITESPACE:
        return "Excessive whitespace."
    elif complaint == Complaint.CONTAINS_CONTROL_CHARS:
        return "Contains control characters: newlines, tabs, or backspaces."
    elif complaint == Complaint.CONTAINS_CONTROL_CHARS_ABS:
        return "Contains control characters: newlines or tabs."
    # elif complaint == 29
    #     return "???"
    elif complaint == Complaint.TRAILING_PUNCTUATION:
        return "Ends with punctuation."
    elif complaint == Complaint.CONTAINS_NUMBER:
        return "Contains a number."
    elif complaint == Complaint.BAD_TEX_ACCENT:
        return "Contains TeXism that is not allowed."
    elif complaint == Complaint.TILDE_AS_HARD_SPACE:
        return "Tilde as hard space."
    elif complaint == Complaint.UNNECESSARY_SPACE_IN_PARENS:
        return "Unnecessary space inside parentheses."
    elif complaint == Complaint.MUST_BE_ENGLISH:
        return "Does not appear to be in English."
    elif complaint == Complaint.EXTRA_WHITESPACE_ABS:
        return "Paragraphs begin or end with whitespace."
    elif complaint == Complaint.TOO_LONG:
        return "Too long."
    elif complaint == Complaint.MUST_CONTAIN_DIGITS:
        return "No digits found."
    elif complaint == Complaint.MUST_CONTAIN_LETTERS:
        return "No letters found."
    elif complaint == Complaint.CONTAINS_URL:
        return "Contains a URL."
    elif complaint == Complaint.CONTAINS_DOI:
        return "Contains a DOI."
    elif complaint == Complaint.CONTAINS_ACCEPTED:
        return "Contains 'ACCEPTED'."
    elif complaint == Complaint.CONTAINS_SUBMITTED:
        return "Contains 'SUBMITTED'."
    elif complaint == Complaint.MUST_CONTAIN_YEAR:
        return "Missing year."
    elif complaint == Complaint.CONTAINS_BIBTEX:
        return "Contains bibtex."
    elif complaint == Complaint.CONTAINS_DOI2:
        return "Contains 'DOI'."
    elif complaint == Complaint.CONTAINS_ARXIV_DOI:
        return "Contains 'arxiv-doi'."
    elif complaint == Complaint.BAD_DOI_PREFIX:
        return "Contains unnecessary prefix."
    elif complaint == Complaint.INSUFFICIENT_ALPHA:
        return "Insufficient text."
    elif complaint == Complaint.LLM_AUTHOR_DETECTED:
        return "LLM author detected."
    elif complaint == Complaint.INVALID_DOI:
        return "Invalid DOI."
    else:
        return "(Unknown issue)"


def complaint2disposition(complaint: Complaint) -> Disposition:
    if complaint == Complaint.CANNOT_BE_EMPTY:
        return HOLD
    elif complaint == Complaint.MUST_CONTAIN_LETTERS:
        return HOLD
    elif complaint == Complaint.MUST_CONTAIN_DIGITS:
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

# NOTE: we can't use re.compile here because we use the re.IGNORECASE flags in add_complaints_matching

# utf8_in_latin1_re = re.compile("[\u00a0-\u00df][\u0080-\u00bf]+")
utf8_in_latin1_re = r"[\u00a0-\u00df][\u0080-\u00bf]+"

# \p{C} would require the regex (not re) module.
# control_chars_re = re.compile("\p{C}+") # looking for "Unicode control characters"
# Looking just for control characters < 32 decimal:
# control_chars_re = re.compile("[\u0000-\u001f]+")
control_chars_re = r"[\u0000-\u001f]+"

# Allow newlines (\n = u\000a) in abstracts
# control_chars_for_abs_re = re.compile("[\u0000-\u0009\u000b-\u001f]+")
control_chars_for_abs_re = r"[\u0000-\u0009\u000b-\u001f]+"
    

############################################################
# Check report objects are a string (disposition)
# and a list of complaints
# Each complaint is a string and a list of contexts.


class MetadataCheckReport:
    def __init__(self):
        self.disposition: Disposition = OK
        self.complaints: Set[Complaint] = set()
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
        return self.offsets     # no copy !?
    
    def get_complaints(self) -> Set[Complaint]:
        return self.complaints


############################################################

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
# This is the main function

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
    if metadata.acm_class is not None:
        result[ACM_CLASS] = check_acm_class(metadata.acm_class)
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
# TODO: offsets to highlight the problem?

def all_brackets_balanced(s: str) -> bool:
    pending_brackets = []
    for c in s:
        if c == "(":
            pending_brackets.append(")")
        elif c == "[":
            pending_brackets.append("]") # 
        elif c == "{":
            pending_brackets.append("}")
        elif (len(pending_brackets) > 0
              and (c == pending_brackets[-1]
                   or (c == ")" and pending_brackets[-1] == "]")
                   or (c == "]" and pending_brackets[-1] == ")")
                   )):
            # Pop one
            pending_brackets = pending_brackets[:-1]
        elif c in ")}]":
            return False
    #
    return len(pending_brackets) == 0

# assert( all_brackets_balanced( "(())[({})] [] {}" ) )
# assert( not all_brackets_balanced( "test ] test" ) )

# assert( all_brackets_balanced( "The open interval [0,1)" ) )



############################################################

def add_complaints_matching(regex: str, v: str, complaint: Complaint, report: MetadataCheckReport):
    for m in re.finditer(regex, v, re.IGNORECASE):
        report.add_complaint(complaint, (m.start(), m.end()))

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
        add_complaints_matching(r"[^ \t\n,][ \t][ \t]+[^ \t\n,]", v, Complaint.EXTRA_WHITESPACE, report)
    else:
        add_complaints_matching(r"[^ \t,][ \t][ \t]+[^ \t,]", v, Complaint.EXTRA_WHITESPACE, report)    
    #
    # Problems: space comma; comma (spaces) comma;
    # DO NOT fix "comma alpha" (e.g. f(a,b) !)
    # JHY: these should be "fixable": s/\s*,\s*,\s*/, / and s/\s*,\s*/, / !
    # add_complaints_matching(r"\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+[a-zA-Z]?|\s*,(\s*,)+", v, Complaint.EXTRA_WHITESPACE, report)
    add_complaints_matching(r"\s+,(\s*,)*[a-zA-Z]?|\s*,(\s*,)+", v, Complaint.EXTRA_WHITESPACE, report)    

    # Careful: parens can be preceded by letters
    # also, parens can be followed by whitespace or punctuation
    # Stop complaining about "O(n)" and "sin(x)"!
    # add_complaints_matching(r"[a-zA-Z]\(", v, Complaint.BAD_CHARACTER, report)
    # Also letters, e.g. H2SO4
    # e.g. Ca10(PO4)6(OH)2 – Hydroxyapatite
    # add_complaints_matching(r"\)[a-zA-Z]", v, Complaint.BAD_CHARACTER, report)        
    
    add_complaints_matching(r"\(\s", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report)
    add_complaints_matching(r"\s\)", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report)

def check_bad_whitespace_for_abs(v: str, report: MetadataCheckReport):
    check_bad_whitespace(v, report, True)
    
def check_starts_with_lowercase(v: str, report: MetadataCheckReport):
    """
    Detect fields (especially titles) which start with a lower case char, eg "bad title"
    TODO: Do nothing smart with "k-means", "eSpeak", or "tugEMM".
    """
    # Don't use add_complaints_matching - it is case-insensitive!
    if re.match(r"^[a-z]", v):
        report.add_complaint(Complaint.BEGINS_WITH_LOWERCASE, (0, 1))
    #
    

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

# ) must be allowed
# *, #, ^, @ are problematic in authors, and detected elsewhere
# ENDS_WITH_PUNCTUATION_RE = re.compile("^.*[!$%^&(_=`:;,.?-]$")
ENDS_WITH_PUNCTUATION_RE = r"^.*[!$%^&(_=`:;,.?-]$"

def check_ends_with_punctuation(v: str, report: MetadataCheckReport):
    """
    Detect common punctuation which should not appear at the end of the authors list
    """
    # if not v.endswith("et al."):
    add_complaints_matching(ENDS_WITH_PUNCTUATION_RE, v, Complaint.TRAILING_PUNCTUATION, report)

def check_language_is_not_english(s: str, report: MetadataCheckReport):
    """
    use gcld3 to detect the "primary" language (abstract only)

    Add a Complaint to report if the primary language appears to be
    something other than English.
    """
    if len(s) < MIN_CHARS_FOR_LID:
        return                  #
    # Not very reliable with < 50 chars...
    lid = gcld3.NNetLanguageIdentifier(MIN_CHARS_FOR_LID, 1000)  # min, max num bytes
    result = lid.FindLanguage(s)
    if result.is_reliable and result.language != "en":
        # No offsets available!
        report.add_complaint(Complaint.MUST_BE_ENGLISH)
    #

    

############################################################


def check_title(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint(Complaint.CANNOT_BE_EMPTY)
    elif len(v) < MIN_TITLE_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
    elif len(v) > MAX_TITLE_LEN:
        report.add_complaint(Complaint.TOO_LONG)
    else:
        pass
    #
    add_complaints_matching(r"^title:?\b", v, Complaint.BEGINS_WITH_TITLE, report)
    #
    add_complaints_matching(r"\\\\", v, Complaint.CONTAINS_LINEBREAK, report)
    #
    if looks_like_all_caps(v):
        report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
    elif long_word_caps(v):
        report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
    #
    check_starts_with_lowercase(v, report)
    #
    add_complaints_matching(r"\\#", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\%", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\href{", v, Complaint.CONTAINS_TEX, report)
    add_complaints_matching(r"\\url{", v, Complaint.CONTAINS_TEX, report)
    #
    # for pat in [
    #         r"\\emph",
    #         r"\\uline",
    #         r"\\textbf",
    #         r"\\texttt",
    #         r"\\textsc",
    # ]:
    #     if contains_outside_math(pat, v):
    #         add_complaints_matching(pat, v, Complaint.CONTAINS_TEX, report)
    #     #
    #
    check_bad_whitespace(v, report)
    #
    check_html_elements(v, report)
    # 
    if not all_brackets_balanced(v):
        report.add_complaint(Complaint.UNBALANCED_BRACKETS)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    # not implemented: titles MAY end with punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report


def check_authors(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # (Field must not be blank)
    if len(v) < MIN_AUTHORS_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
    # NO max authors len!
    # elif len(v) > MAX_AUTHORS_LEN:
    #     report.add_complaint(TOO_LONG)
    #
    add_complaints_matching(r"\\\\", v, Complaint.CONTAINS_TEX, report)
    add_complaints_matching(r"\*", v, Complaint.BAD_CHARACTER, report)
    add_complaints_matching(r"#", v, Complaint.BAD_CHARACTER, report)
    add_complaints_matching(r"[^\\]\^", v, Complaint.BAD_CHARACTER, report)
    add_complaints_matching(r"@", v, Complaint.BAD_CHARACTER, report)                
    #
    check_bad_whitespace(v, report)
    #
    add_complaints_matching(r"anonymous", v, Complaint.CONTAINS_ANONYMOUS, report)
    add_complaints_matching(r"corresponding", v, Complaint.CONTAINS_CORRESPONDING, report)
    #
    for s in ("\\dag", "\\ddag", "\\textdag", "\\textddag"):
        add_complaints_matching(s, v, Complaint.CONTAINS_TEX, report)                
    #
    add_complaints_matching(r"^authors?:?\b", v, Complaint.BEGINS_WITH_AUTHOR, report)
    #
    check_html_elements(v, report)
    #
    if not all_brackets_balanced(v):
        report.add_complaint(Complaint.UNBALANCED_BRACKETS)
    #
    add_complaints_matching(r"\( ", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report)
    add_complaints_matching(r" \)", v, Complaint.UNNECESSARY_SPACE_IN_PARENS, report)    

    # This is wrong !
    # Parse the authors list first, then complaing about ";" in any author name
    # if re.search(r";", v) and not re.search(r"\(.*;.*\)", v):
    #     # "use commas, not ';' to separate authors"
    #     report.add_complaint(Complaint.CONTAINS_SEMICOLON)
    
    # Are tildes allowed anywhere? Yes, as a TeX accent
    # (Consider: only check names?)
    add_complaints_matching(r"[^\\]~", v, Complaint.TILDE_AS_HARD_SPACE, report)
    #
    # Authors list can NOT end with punctuation
    if not v.endswith("et al."):
        check_ends_with_punctuation(v, report)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
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

    # TODO: need offsets from parse_author_affil ...

    parsed_authors = parse_author_affil(v)  # => List[List[str]]
    for author in parsed_authors:
        # for "Cecil B. Demille", firstname should be "Cecil B." and keyname shoudl be "Demille"
        # first is "keyname" (surname?), second is fist name(s), third is suffix
        keyname = author[0]
        firstname = author[1]
        suffix = author[2]

        check_one_author(report, keyname, firstname, suffix)  # updates report
    # end for author in parsed_authors

    return report


def check_one_author(report, keyname, firstname, suffix) -> None:
    # Bad things result in side-effecting calls to report

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
            # Check for bad standalone LLM names
            found_llm_author = False
            for badword in (
                    "Llama", "Olamma", "Gemini", "Claude", "Bert", "Bart", "Grok",
                    "ChatGPT",
                    "GPT-3", "GPT-3.",
                    "GPT-4", "GPT-4.",
                    "GPT-5", "GPT-5."
                    "PalM2",
            ):
                if badword.lower() == keyname.lower():
                    # TODO: offsets
                    report.add_complaint(Complaint.LLM_AUTHOR_DETECTED)
                    found_llm_author = True
                #
            #
            if not found_llm_author:
                # TODO: offsets
                report.add_complaint(Complaint.CONTAINS_LONE_SURNAME)
            #
        #
    #
    # Don't reject Sylvie ROUX nor S ROUX
    # if re.match("^[A-Z]{3,}$", keyname) and re.match("^[A-Z]{3,}$", firstname):
    #     report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION, f"'{name}'")
    #
    # Allow "Chandrasekar R" but not "Chandra R."
    # if re.match(r"^[A-Z]\.$", keyname):
    #     report.add_complaint(CONTAINS_INITIALS, f"'{name}'")
    # if keyname and re.match(r"\.$", keyname):
    #     report.add_complaint(Complaint.TRAILING_PUNCTUATION)
    # elif (not keyname) and re.match(r"\.$", surname):
    #     report.add_complaint(Complaint.TRAILING_PUNCTUATION)
    #
    # Reject e. e. cummings and "evans". Don't reject J von
    # if keyname == keyname.lower() and (
    #     firstname is None or firstname == firstname.lower()
    # ):
    #     report.add_complaint(NO_CAPS_IN_NAME, f"'{name}'")

    if re.search( ";", name ):
        report.add_complaint(Complaint.CONTAINS_SEMICOLON)

    if (
        re.search(r"\[|]", keyname)
        or re.search(r"\[|]", firstname)
        or re.search(r"\[|]", suffix)
    ):
        # TODO: offsets
        report.add_complaint(Complaint.BAD_CHARACTER)
    #
    if (
        re.search("[0-9]", keyname)
        or re.search("[0-9]", firstname)
        or re.search("[0-9]", suffix)
    ):
        # TODO: offsets
        report.add_complaint(Complaint.CONTAINS_NUMBER)
    #
    # match A. and A.B. but not IV or other roman numerals
    # if (
    #     re.match(r"^[A-Z]\.$", suffix)
    #     or re.match(r"^[A-Z]\.[A-Z]\.$", suffix)
    #     or re.match(r"^[A-Z]\.[A-Z]\.[A-Z]\.$", suffix)
    # ):
    #     report.add_complaint(CONTAINS_INITIALS, f"Initials in '{name}'")
    #
    for badmessage, badpattern in (
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
    ):
        if (
            re.search(badpattern, keyname, re.IGNORECASE)
            or re.search(badpattern, firstname, re.IGNORECASE)
            or re.search(badpattern, suffix, re.IGNORECASE)
        ):
            # TODO: offsets
            report.add_complaint(Complaint.CONTAINS_AFFILIATION)
        #
    # end for affiliations

    for badmessage, badpattern in (
            # LLM "names"
            ("chatgpt", r"\bchatgpt?\b"),
            ("GPT-4", r"\bGPT-4"),  # Also match 4o, etc
            ("GPT-5", r"\bGPT-5"),
            ("GPT-3.x", r"\bGPT-3\."),
            ("GPT-3.5", r"\bGPT-3.5\b"),
            ("GPT-4.x", r"\bGPT-4\."),  # Should also match 4.x
            ("GPT-5.x", r"\bGPT-5\."),  # Should also match 5.x
            ("PaLM2", r"\bPalM2\b"),
            # Claude and Bert are common names; see above
            # Is Gemini too common?
            ("Gemini", r"\bGemini\b"),
    ):
        if (
            re.search(badpattern, name, re.IGNORECASE)
        ):
            # TODO: offsets
            report.add_complaint(Complaint.LLM_AUTHOR_DETECTED)
        #
    #


def check_abstract(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint(Complaint.CANNOT_BE_EMPTY)
    elif len(v) < MIN_ABSTRACT_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
    elif len(v) > MAX_ABSTRACT_LEN:
        report.add_complaint(Complaint.TOO_LONG)
    #
    # Only match beginning!
    add_complaints_matching(r"^abstract\b", v, Complaint.BEGINS_WITH_ABSTRACT, report)
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
    # Now in check_bad_whitespace shared code
    if looks_like_all_caps(v):
        report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION) # TODO
    #
    check_starts_with_lowercase(v, report)
    #
    add_complaints_matching(r"\\#", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\%", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\href{", v, Complaint.CONTAINS_TEX, report)
    add_complaints_matching(r"\\url{", v, Complaint.CONTAINS_TEX, report)
    # JHY: \begin{equation}, etc are permitted , but not "\begin" ...
    add_complaints_matching(r"\\begin[^{]", v, Complaint.CONTAINS_TEX, report)
    #
    # for pat in [
    #         r"\\emph",
    #         r"\\uline",
    #         r"\\textbf",
    #         r"\\texttt",
    #         r"\\textsc",
    # ]:
    #     if contains_outside_math(pat, v):
    #         # Marginal...
    #         # add_complaints_matching(pat, v, Complaint.CONTAINS_BAD_STRING, report)
    #         # TODO: ?
    #         pass
    #     #
    #
    check_bad_whitespace_for_abs(v, report)
    #
    check_html_elements(v, report)
    #
    if not all_brackets_balanced(v):
        report.add_complaint(Complaint.UNBALANCED_BRACKETS)
    #
    #
    check_language_is_not_english(v, report)
    #
    # SUBTLE: don't complain about \n newlines in abstracts!
    add_complaints_matching(control_chars_for_abs_re, v, Complaint.CONTAINS_CONTROL_CHARS_ABS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    # note: abstracts MAY end in punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report


def check_comments(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # No check for too short (Empty comments are ok)
    # No check for too long (!?)
    add_complaints_matching(r"\\\\", v, Complaint.CONTAINS_TEX, report)
    #
    if looks_like_all_caps(v):
        report.add_complaint(Complaint.EXCESSIVE_CAPITALIZATION)
    #
    add_complaints_matching(r"\\#", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\%", v, Complaint.UNNECESSARY_ESCAPE, report)
    add_complaints_matching(r"\\href{", v, Complaint.CONTAINS_TEX, report)
    add_complaints_matching(r"\\url{", v, Complaint.CONTAINS_TEX, report)
    #
    # for pat in [
    #         r"\\emph",
    #         r"\\uline",
    #         r"\\textbf",
    #         r"\\texttt",
    #         r"\\textsc",
    # ]:
    #     if contains_outside_math(pat, v):
    #         add_complaints_matching(pat, v, Complaint.CONTAINS_TEX, report)
    #     #
    #
    check_bad_whitespace(v, report)
    #
    if not all_brackets_balanced(v):
        report.add_complaint(Complaint.UNBALANCED_BRACKETS)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    # TODO: check that language is English?

    return report


def check_report_num(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_REPORT_NUM_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
        return report
    elif len(v) > MAX_REPORT_NUM_LEN:
        report.add_complaint(Complaint.TOO_LONG)
    #
    add_complaints_matching(r"http:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"https:", v, Complaint.CONTAINS_URL, report)    
    # add_complaints_matching(r"doi", v, Complaint.CONTAINS_DOI, report) #
    #
    # was not match r"^[0-9]*$"
    if not re.search(r"[A-Z]", v):
        report.add_complaint(Complaint.MUST_CONTAIN_LETTERS)
    if not re.search(r"[0-9]", v):
        report.add_complaint(Complaint.MUST_CONTAIN_DIGITS)
    #
    check_bad_whitespace(v, report)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    return report


def check_journal_ref(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_JOURNAL_REF_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
    elif len(v) > MAX_JOURNAL_REF_LEN:
        report.add_complaint(Complaint.TOO_LONG)
    #
    # TODO: check for author name(s) in jref
    # TODO: check for paper title in jref
    add_complaints_matching(r"http:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"https:", v, Complaint.CONTAINS_URL, report)    
    add_complaints_matching(r"doi", v, Complaint.CONTAINS_DOI, report) # ?
    # Interesting:
    add_complaints_matching(r"^[0-9][0-9].[0-9]+/[^ ]*$", v, Complaint.CONTAINS_DOI, report) # 
    add_complaints_matching(r"accepted", v, Complaint.CONTAINS_ACCEPTED, report)
    add_complaints_matching(r"submitted", v, Complaint.CONTAINS_SUBMITTED, report)
    #
    check_bad_whitespace(v, report)
    #
    # Removed Oct 2025
    # if not re.search("[12][90][0-9][0-9]", v):
    #     report.add_complaint(Complaint.MUST_CONTAIN_YEAR)
    #
    for s in ("title", "booktitle", "inproceedings"):
        add_complaints_matching(f"{s}=", v, Complaint.CONTAINS_BIBTEX, report)
        #
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    return report


def check_doi(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_DOI_LEN:
        report.add_complaint(Complaint.TOO_SHORT)
        return report
    elif len(v) > MAX_DOI_LEN:
        report.add_complaint(Complaint.TOO_LONG)
        # Don't return
    #
    # Validate the DOI(s) found in this field (first!)
    # TODO: how many submissions contain multiple dois?
    start = 0
    for doi in v.split():
        start = v.index(doi, start) # should never fail
        end = start + len(doi)
        if not re.match(r"^[0-9][0-9]*\.[0-9][0-9]*/[A-Za-z0-9():;._/-]*$", doi):
            report.add_complaint(Complaint.INVALID_DOI, (start, end))
        #
    #
    add_complaints_matching(r"http:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"https:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"doi", v, Complaint.CONTAINS_DOI2, report)
    #
    # If it contains "doi", it also contains "arxiv-doi" !
    # if re.search("arxiv-doi", v):
    #     report.add_complaint(CONTAINS_BAD_STRING, "arxiv-doi")
    #
    check_bad_whitespace(v, report)

    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)

    return report


def check_msc_class(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    add_complaints_matching(r"http:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"https:", v, Complaint.CONTAINS_URL, report)
    #
    add_complaints_matching(r"arxiv-doi", v, Complaint.CONTAINS_ARXIV_DOI, report)    
    #
    check_bad_whitespace(v, report)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    add_complaints_matching(r";", v, Complaint.CONTAINS_SEMICOLON, report)
    #
    # TODO: don't show these to editors?
    # for s in ("MSC *class", "MSC number"):
    #     if re.search(f"{s}=", v, re.IGNORECASE):
    #         report.add_complaint(CONTAINS_BAD_STRING, s)
    #         break
    #     #
    # #

    return report


def check_acm_class(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    add_complaints_matching(r"http:", v, Complaint.CONTAINS_URL, report)
    add_complaints_matching(r"https:", v, Complaint.CONTAINS_URL, report)
    #
    add_complaints_matching(r"doi", v, Complaint.CONTAINS_DOI2, report)    
    #
    check_bad_whitespace(v, report)
    #
    add_complaints_matching(control_chars_re, v, Complaint.CONTAINS_CONTROL_CHARS, report)
    add_complaints_matching(utf8_in_latin1_re, v, Complaint.BAD_UNICODE_ENCODING, report)
    #
    add_complaints_matching(r";", v, Complaint.CONTAINS_SEMICOLON, report)
    #
    return report

# Check for \n but not \n<space><space> (a paragraph break) in abstract?
# \n is not allowed in fields other than the abstract, right?

