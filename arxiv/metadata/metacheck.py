
import re

from typing import Dict

import gcld3

from arxiv.authors import parse_author_affil

from arxiv.metadata import FieldName
from arxiv.metadata import Disposition
from arxiv.metadata.all_caps_words import KNOWN_WORDS_IN_ALL_CAPS

############################################################
TITLE = FieldName.TITLE
AUTHORS = FieldName.AUTHORS
ABSTRACT = FieldName.ABSTRACT
COMMENTS = FieldName.COMMENTS
REPORT_NUM = FieldName.REPORT_NUM
JOURNAL_REF = FieldName.JOURNAL_REF
DOI = FieldName.DOI

OK = Disposition.OK
WARN = Disposition.WARN
HOLD = Disposition.HOLD

############################################################
# Some constants

MIN_TITLE_LEN = 5
MIN_AUTHORS_LEN = 5
MIN_ABSTRACT_LEN = 5
# No MIN_COMMENTS_LEN
MIN_REPORT_NUM_LEN = 4
MIN_JOURNAL_REF_LEN = 5
MIN_DOI_LEN = 10                # such as: 10.1234/5678 

# Language identification is pretty fragile, particularly on short abstracts.
MIN_CHARS_FOR_LID = 20

############################################################

def combine_dispositions(d1:Disposition, d2:Disposition) -> Disposition:
    if d1 == HOLD or d2 == HOLD:
        return HOLD
    elif d1 == WARN or d2 == WARN:
        return WARN
    else:
        return OK

def contains_outside_math(s1:str, s2:str) -> bool:
    """ Looks for s1, outside of TeX math
    Not perfect: fails to find xyzzy in $math$ xyzzy $$more math$$.
    """
    if re.search(s1, s2, re.IGNORECASE) \
       and not re.search("[$].*"+s1+".*[$]", s2, re.IGNORECASE):
        return True
    else:
        return False
       

############################################################
# This is the main function

def check(metadata:Dict[FieldName,str]): 
    result = {} 
    for (k,v) in metadata.items():
        if k == TITLE:
            result[k] = check_title(v)
        elif k == AUTHORS:
            result[k] = check_authors(v)
        elif k == ABSTRACT:
            result[k] = check_abstract(v)
        elif k == COMMENTS:
            result[k] = check_comments(v)
        elif k == REPORT_NUM:
            result[k] = check_report_num(v)
        elif k == JOURNAL_REF:
            result[k] = check_journal_ref(v)
        elif k == DOI:
            result[k] = check_doi(v)
        else:
            raise UnknownMetadataException(f"Unknown metadata field {k}: {v}")
    #
    return result

def looks_like_all_caps(s: str) -> bool:
    """
    Returns true if s appears to have all/excessive capitals. The
    exact threshold is heuristic based on looking at submissions over
    March 2010.
    """
    num_caps = sum([ c.isupper() for c in s])
    num_lower = sum([ c.islower() for c in s])
    if num_caps > num_lower * 2 + 7:
        return True
    else:
        return False


def long_word_caps(s: str) -> bool:
    """
    Returns true (was: a list of long words) if s appears to have
    two or more words which are
    * at least 6 characters long,
    * in all caps,
    * contain at least one capitalized letter (not digits or punctuation!), 
    * and which are not in our list of KNOWN_WORDS_IN_ALL_CAPS.
    """
    num_matches = 0
    for word in s.split():
        if len(word) >= 6 and \
           word.upper() == word and \
           word.lower() != word and \
           word not in KNOWN_WORDS_IN_ALL_CAPS:
            num_matches += 1
        #
    #
    return (num_matches > 1):

def smart_starts_with_lowercase_check(s: str) -> bool:
    """
    Detect titles which start with a lower case char, eg "bad title"
    but do not reject "eSpeak: A New World"
    """

    if len(s) < 1:
        return False
    if re.match( "[a-z]", s):
        if re.match( "[a-z][A-Z][a-zA-Z]*: [A-Z]", s):
            return False
        else:
            return True
    else:
        return False
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
        elif len(pending_brackets) > 0 and c == pending_brackets[-1]:
            pending_brackets = pending_brackets[:-1]
        elif c in ")}]":
            return False
    #
    return (len(pending_brackets) == 0)

def language_is_not_english(s: str) -> bool:
    """
    use gcld3 to detect the "primary" language (abstract only)

    return True only if the primary language appears to be
    something other than English.
    """
    if len(s) < MIN_CHARS_FOR_LID:
        return False            # 
    # Not very reliable with < 50 chars...
    lid = gcld3.NNetLanguageIdentifier(MIN_CHARS_FOR_LID, 1000) # min, max num bytes
    result = lid.FindLanguage(s)
    if result.is_reliable and result.language != "en":
        return True
    else:
        return False

HTML_ELEMENTS = [
    "<p[^a-z]", "</p>"
    "<div[^a-z]", "</div>",
    "<br[^a-z]", "</br>",
    "<a[^a-z]", "</a>",
    "<img[^a-z]", "</img>",
    "<sup[^a-z]", "</sup>",
    "<sub[^a-z]", "</sub>",
    "<table[^a-z]", "</table>",
]
    
def contains_html_elements(s: str) -> bool:
    """
    Detect common HTML elements:
    <p> <div> <br> <a> <img> <sup> <sub> and <table>
    
    - but not <a> <b> ... <x> <y> or <z>
    """
    for element in HTML_ELEMENTS:
        if re.search(element, s, re.IGNORECASE):
            return True
        #
    #
    return False

# ) must be allowed
# *, #, ^, @ are problematic in authors, and detected elsewhere
ENDS_WITH_PUNCTUATION_RE = re.compile( "[!$%^&(_=`:;,.?-]$" )

def ends_with_punctuation(s: str) -> bool:
    """
    Detect common punctuation which should not appear at the end of the authors lsit
    """
    return ENDS_WITH_PUNCTUATION_RE.search(s)


############################################################

def check_title(v: str) -> (str, str):
    disposition = OK
    complaints = []
    if v is None or v == "":
        disposition = combine_dispositions(disposition, HOLD)
        complaints.append("Title cannot be empty")
    elif len(v) < MIN_TITLE_LEN:
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: too short")
    #
    if re.match( "title", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: begins with 'title'")
    #
    # TODO: leading, trailing, excess space?
    if re.search( r"\\\\", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains TeX line break")
    #
    if looks_like_all_caps(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: excessive capitalization")
    elif long_word_caps(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: excessive capitalization (words)")
    #
    if smart_starts_with_lowercase_check(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: starts with a lower case letter")
    #
    if re.search( r"\\href{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains TeX \\href")
    #
    if re.search( r"\\url{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains TeX \\url")
    #
    if contains_outside_math( r"\\emph", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains unnecessary escape: \\%")
    #
    if contains_html_elements(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: contains HTML")
    #
    if not all_brackets_balanced(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Title: unbalanced brackets")
    #
    # not implemented: titles MAY end with punctuation
    # not implemented: check for arXiv or arXiv:ID
    return disposition, complaints

def check_authors(v: str) -> (str, str):
    disposition = OK
    complaints = []
    # (Field must not be blank)
    if len(v) < MIN_AUTHORS_LEN:
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: too short")
    #
    if re.search( r"\\\\", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains TeX line break")
    #
    if re.search( r"\*", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains bad character '*'")
    #
    if re.search( r"#", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains bad character '#'")
    #
    if re.search( r"\^", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains bad character '^'")
    #
    if re.search( r"@", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains bad character '@'")
    #
    if re.match( r"^\s", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: leading whitespace")
    #
    if re.search( r"\s$", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: trailing whitespace")
    #
    if re.search( r"\s\s", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: excess whitespace")
    #
    # This should also match ", ," ?
    if re.search( r"\s,", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: whitespace before comma")
    #
    if re.search( r"anonym", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: anonymous submissions not accepted")
    #
    if re.search( r"corresponding", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains 'corresponding'")
    #
    for s in ("\\dag", "\\ddag", "\\textdag", "\\textddag"):
        if re.match( s, v, re.IGNORECASE):
            disposition = combine_dispositions(disposition, WARN)
            complaints.append("Authors: contains dagger symbol")
            break
        #
    #
    if re.match( "authors", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: begins with 'authors'")
    elif re.match( "author", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: begins with 'author'")
    #
    if contains_html_elements(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: contains HTML")
    #
    if not all_brackets_balanced(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: unbalanced brackets")
    #
    # Do I need to parse the authors list first?
    if re.search( r";", v) and not re.search( "(.*;.*)", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: use commas, not ';' to separate authors")
    #
    # Authors list can NOT end with punctuation
    if ends_with_punctuation(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: ends with punctuation")
    #
    
    # Parse authors, check authors names - but not affiliations - for:
    # ALL CAPS
    # single word in all CAPS (not really done)
    # [...] (in author name)
    # Numbers (but Jennifer 8 Lee!)
    # IEEE (confusable with affiliation)
    # phd, prof, dr
    # Single initial after parsing authors?
    # TODO: letters after name (BUT Indian names like RS, etc?)
    # TODO: extra curlies in TeX accents, e.g.: {\'e}
    # (TODO: allow all Unicode ?)
    # TODO: urls

    # TODO: maybe remove duplicates from the complaints list
    
    parsed_authors = parse_author_affil(v) # => List[List[str]]
    for author in parsed_authors:
        # first is "keyname" (surname?), second is fist name(s), third is suffix
        keyname = author[0]
        firstname = author[1]
        suffix = author[2]

        complaints, disposition = check_one_author(complaints, disposition, keyname, firstname, suffix)
    # end for author in parsed_authors

    return disposition, complaints

def check_one_author(complaints, disposition, keyname, firstname, suffix):
            
    # Some quick special cases to skip:
    if keyname.lower() == "author" and firstname == "" and suffix == "":
        return (complaints, disposition)
    if keyname.lower() == "authors" and firstname == "" and suffix == "":
        return (complaints, disposition)
    if keyname == ":" and firstname == "" and suffix == "":
        return (complaints, disposition)
    if firstname == "":
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: lone surname")
    #
    # Don't reject Sylvie ROUX nor S ROUX
    if re.match("^[A-Z]{3,}$", keyname) and \
       re.match("^[A-Z]{3,}$", firstname):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Author name is in all caps")
    #
    if re.match(r"^[A-Z]$", keyname) or \
       re.match(r"^[A-Z]\.$", keyname):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Author: found initial not surname")
    #
    # Reject e. e. cummings and "evans". Don't reject J von
    if keyname == keyname.lower() and \
       (firstname is None or firstname == firstname.lower()):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: no caps in name")
    #
    if re.search(r"\[|]", keyname) or \
       re.search(r"\[|]", firstname) or \
       re.search(r"\[|]", suffix):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: name should not contain brackets")
    #
    if re.search("[0-9]", keyname) or \
       re.search("[0-9]", firstname) or \
       re.search("[0-9]", suffix):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: name should not contain digits")
    #
    # match A. and A.B. but not AB (or RS)
    # This may be broken due to the rest of the author name parser
    if re.match("^[A-Z].$", suffix) or \
       re.match("^[A-Z].[A-Z].$", suffix) or \
       re.match("^[A-Z].[A-Z].[A-Z].$", suffix):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Authors: name suffix should not contain initials")
    #
    for badword in (
            ";",
            "IEEE", "phd", "prof", "[^a-z]dr[^a-z]",
            "Physics", "Math[. ]", "Math$",
            "Inst", "Institute",
            "Dept", "Department",
            "Univ", "University",
            "chatgpt", "^llama$", "^gemini$", "GPT-3.5", "GPT-4", "GPT-4o",
            "PaLM2"
            # Claude and Bert are too common
    ):
        if re.search(badword, keyname, re.IGNORECASE) or \
           re.search(badword, firstname, re.IGNORECASE) or \
           re.search(badword, suffix, re.IGNORECASE):
            disposition = combine_dispositions(disposition, WARN)
            complaints.append(f"Authors: name should not contain {badword}")
        #
    # end for badword in badwords

    return (complaints, disposition)


def check_abstract(v: str) -> (str, str):
    disposition = OK
    complaints = []
    if v is None or v == "":
        disposition = combine_dispositions(disposition, HOLD)
        complaints.append("Abstract cannot be empty")
    elif len(v) < MIN_ABSTRACT_LEN:
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: too short")
    #
    if re.match( "abstract", v, re.IGNORECASE):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: begins with 'abstract'")
    #
    if re.search( r"\\\\", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains TeX line break")
    #
    if looks_like_all_caps(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: excessive capitalization")
    # elif long_word_caps(v):
    #     disposition = combine_dispositions(disposition, WARN)
    #     complaints.append("Abstract: excessive capitalization (words)")
    #
    # JHY : this is not very smart
    if smart_starts_with_lowercase_check(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: starts with a lower case letter")
    #
    if re.search( r"\\href{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains TeX \\href")
    #
    if re.search( r"\\url{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains TeX \\url")
    #
    if contains_outside_math( r"\\emph", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains unnecessary escape: \\%")
    #
    if contains_html_elements(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: contains HTML")
    #
    if not all_brackets_balanced(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract: unbalanced brackets")
    #
    if re.search( r"\\begin", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract contains \begin")
    #
    if language_is_not_english(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Abstract does not appear to be English")
    #
    # not implemented: abstract MAY end in punctuation
    # not implemented: check for arXiv or arXiv:ID
    return disposition, complaints

def check_comments(v: str) -> (str, str):
    disposition = OK
    complaints = []
    # Empty comments are ok!
    if re.search( r"\\\\", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains TeX line break")
    #
    if looks_like_all_caps(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: excessive capitalization")
    #
    if re.search( r"\\href{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains TeX \\href")
    #
    if re.search( r"\\url{", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains TeX \\url")
    #
    if contains_outside_math( r"\\emph", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: contains unnecessary escape: \\%")
    #
    if not all_brackets_balanced(v):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append("Comments: unbalanced brackets")
    #
    # TODO: check that language is English?
    
    return disposition, complaints

def check_report_num(v: str) -> (str, str):
    if len(v) < MIN_REPORT_NUM_LEN:
        return HOLD, ["Report-no: too short"]
    if re.match(r"^[0-9]*$", v):
        return HOLD, ["Report-no: no letters"]
    elif re.match(r"^[A-Za-z-]*$", v):
        return HOLD, ["Report-no: no digits"]
    else:
        return OK, []

def check_journal_ref(v: str) -> (str, str):
    disposition = OK
    complaints = []
    if len(v) < MIN_JOURNAL_REF_LEN:
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: too short" )
    #
    # TODO: check for author name(s) in jref
    # TODO: check for paper title in jref
    if re.search( "http:", v, re.IGNORECASE ) or \
       re.search( "https:", v, re.IGNORECASE ):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: contains URL" )
    #
    if re.search( "doi", v, re.IGNORECASE ):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: contains DOI" )
    #
    if re.search( "accepted", v, re.IGNORECASE ):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: contains 'accepted'" )
    #
    if re.search( "submitted", v, re.IGNORECASE ):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: contains 'submitted'" )
    #
    if not re.search( "[12][90][0-9][0-9]", v ):
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: missing year" )
    #
    if re.search( "inproceedings", v, re.IGNORECASE ) or \
       re.search( "title=", v, re.IGNORECASE ) or \
       re.search( "booktitle=", v, re.IGNORECASE ): # redundant
        disposition = combine_dispositions(disposition, WARN)
        complaints.append( "jref: copy from bibtex" )
    #
    # TODO: "validate input encoding" - what does this mean?
    return disposition, complaints

def check_doi(v: str) -> (str, str):
    if len(v) < MIN_DOI_LEN:
        return WARN, ["doi: too short"]
    if re.search( "http:", v ):
        return WARN, ["doi: contains http:"]
    if re.search( "https:", v ):
        return WARN, ["doi: contains https:"]
    if re.search( "doi:", v ):
        return WARN, ["doi: contains doi:"]
    # Is this right?
    if re.search( "arxiv-doi", v ):
        return WARN, ["doi: contains arxiv-doi"]
    return OK, []

