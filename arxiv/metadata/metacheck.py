
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
# Check report objects are a string (disposition)
# and a list of complaints
# Each complaint is a string and a list of contexts.

class MetadataCheckReport:
    def __init__(self):
        self.disposition = OK
        # map from complaint to context (may be "")
        self.complaints = {}

    def __repr__(self):
        if self.disposition == OK:
            return f"<MetadataCheckReport OK>"
        else:
            return f"<MetadataCheckReport {self.disposition}: {self.get_complaints_strings()}>"
        

    def add_complaint(self, disposition, complaint_string:str, context:str = ""):
        self.disposition = combine_dispositions(self.disposition, disposition)
        if complaint_string in self.complaints:
            self.complaints[complaint_string].append(context)
        else:
            self.complaints[complaint_string] = [context]
        #
             
    def get_disposition(self) -> Disposition:
        return self.disposition
    
    def get_complaints_list(self) -> list[str]:
        return list(self.complaints.keys())

    def get_complaints_strings(self) -> list[str]:
        return "; ".join([
            complaint_string
            if contexts == [""]
            else complaint_string + " (" + ", ".join(contexts) + ")"
            for (complaint_string, contexts) in self.complaints.items()
        ])
    

############################################################
# This is the main function

def check(metadata:Dict[FieldName,str]) -> Dict[FieldName,MetadataCheckReport]: 
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

############################################################
#

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
    * is in all caps (TODO: strip trailing comma ","?)
    * and which are not in our list of KNOWN_WORDS_IN_ALL_CAPS.
    """
    num_matches = 0
    for word in s.split():
        if len(word) >= 6 and \
           re.match( "^[A-Z]*$", word ) and \
           word not in KNOWN_WORDS_IN_ALL_CAPS:
            num_matches += 1
        #
    #
    return (num_matches > 1)

def smart_starts_with_lowercase_check(s: str) -> bool:
    """
    Detect titles which start with a lower case char, eg "bad title" or "a bad title"
    but do not reject "eSpeak: A New World", "tuGEMM: ...", "uGMMS", or "p-Mean"
    """

    if len(s) < 1:
        return False
    if re.match( "[a-z]", s):
        if re.match( "[a-z][a-zA-Z-]*: [A-Z]", s):
            return False
        elif re.match( "[a-z][A-Z][A-Z]* ", s):
            # Matches uGMS
            return False
        elif re.match( "[a-z]-[A-Z]", s):
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
    "<p ", "<p>", "</p>"
    "<div ", "<div", "</div>",
    "<br ", "<br>", "</br>",
    "<a ", "<a>", "</a>",
    "<img ", "<img>", "</img>",
    "<sup ", "<sup>", "</sup>",
    "<sub ", "<sub>", "</sub>",
    "<table ", "<table>", "</table>",
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
ENDS_WITH_PUNCTUATION_RE = re.compile( r"[!$%^&(_=`:;,.?-]$" )
ENDS_WITH_PUNCTUATION_EXCEPTIONS_RE = re.compile( r"[JS]r\.$" )

def ends_with_punctuation(s: str) -> bool:
    """
    Detect common punctuation which should not appear at the end of the authors list
    """
    return ENDS_WITH_PUNCTUATION_RE.search(s) \
        and not ENDS_WITH_PUNCTUATION_EXCEPTIONS_RE.search(s) \

# Look for bad encodings:
# [\u00C0-\u00DF][\u0080-\u00BF]
# [\u00E0-\u00EF][\u0080-\u00BF][\u0080-\u00BF]
# and
# [\u00F0-\u00F7][\u0080-\u00BF][\u0080-\u00BF][\u0080-\u00BF]

# Simplified to: [\u00C0-\u00DF\u00E0-\u00EF\u00F0-\u00F7][\u0080-\u00BF]

def contains_bad_encoding(s: str) -> bool:
    # Beware: \u0080 is a funny character
    return( re.search( r"[\u00C0-\u00DF\u00E0-\u00EF\u00F0-\u00F7][\u0080-\u00BF]", s ) )

############################################################

# => MetadataReport ?
def check_title(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint( HOLD, "Title cannot be empty")
    elif len(v) < MIN_TITLE_LEN:
        report.add_complaint( WARN, "Title: too short")
    #
    if re.match( r"title\b", v, re.IGNORECASE):
        report.add_complaint( WARN, "Title: begins with 'title'")
    #
    # TODO: leading, trailing, excess space?
    if re.search( r"\\\\", v):
        report.add_complaint( WARN, "Title: contains line break")
    #
    if looks_like_all_caps(v):
        report.add_complaint( WARN, "Title: excessive capitalization")
    elif long_word_caps(v):
        report.add_complaint( WARN, "Title: excessive capitalization (words)")
    #
    if smart_starts_with_lowercase_check(v):
        report.add_complaint( WARN, "Title: starts with a lower case letter")
    #
    if re.search( r"\\href{", v):
        report.add_complaint( WARN, "Title: contains \\href")
    #
    if re.search( r"\\url{", v):
        report.add_complaint( WARN, "Title: contains \\url")
    #
    if contains_outside_math( r"\\emph", v):
        report.add_complaint( WARN, "Title: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        report.add_complaint( WARN, "Title: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        report.add_complaint( WARN, "Title: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        report.add_complaint( WARN, "Title: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        report.add_complaint( WARN, "Title: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        report.add_complaint( WARN, "Title: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        report.add_complaint( WARN, "Title: contains unnecessary escape: \\%")
    #
    if contains_html_elements(v):
        report.add_complaint( WARN, "Title: contains HTML")
    #
    if not all_brackets_balanced(v):
        report.add_complaint( WARN, "Title: unbalanced brackets")
    #
    # not implemented: titles MAY end with punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report

############################################################

def check_authors(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # (Field must not be blank)
    if len(v) < MIN_AUTHORS_LEN:
        report.add_complaint( WARN, "Authors: too short")
    #
    if re.search( r"\\\\", v):
        report.add_complaint( WARN, "Authors: contains line break")
    #
    if re.search( r"\*", v):
        report.add_complaint( WARN, "Authors: contains bad character '*'")
    #
    if re.search( r"#", v):
        report.add_complaint( WARN, "Authors: contains bad character '#'")
    #
    if re.search( r"[^\\]\^", v):
        report.add_complaint( WARN, "Authors: contains bad character '^'")
    #
    if re.search( r"@", v):
        report.add_complaint( WARN, "Authors: contains bad character '@'")
    #
    if re.match( r"^\s", v):
        report.add_complaint( WARN, "Authors: leading whitespace")
    #
    if re.search( r"\s$", v):
        report.add_complaint( WARN, "Authors: trailing whitespace")
    #
    if re.search( r"\s\s", v):
        report.add_complaint( WARN, "Authors: excess whitespace")
    #
    # This should also match ", ," ?
    if re.search( r"\s,", v):
        report.add_complaint( WARN, "Authors: whitespace before comma")
    #
    if re.search( r"anonym", v, re.IGNORECASE):
        report.add_complaint( WARN, "Authors: anonymous submissions not accepted")
    #
    if re.search( r"corresponding", v, re.IGNORECASE):
        report.add_complaint( WARN, "Authors: contains 'corresponding'")
    #
    for s in ("\\dag", "\\ddag", "\\textdag", "\\textddag"):
        if re.match( s, v, re.IGNORECASE):
            report.add_complaint( WARN, "Authors: contains dagger symbol")
            break
        #
    #
    if re.match( r"authors\b", v, re.IGNORECASE):
        report.add_complaint( WARN, "Authors: begins with 'authors'")
    elif re.match( r"author\b", v, re.IGNORECASE):
        report.add_complaint( WARN, "Authors: begins with 'author'")
    #
    if contains_html_elements(v):
        report.add_complaint( WARN, "Authors: contains HTML")
    #
    if not all_brackets_balanced(v):
        report.add_complaint( WARN, "Authors: unbalanced brackets")
    #
    # Do I need to parse the authors list first?
    if re.search( r";", v) and not re.search( "(.*;.*)", v):
        report.add_complaint( WARN, "Authors: use commas, not ';' to separate authors")
    #
    # Authors list can NOT end with punctuation (except for Jr., Sr.
    if ends_with_punctuation(v):
        report.add_complaint( WARN, "Authors: ends with punctuation")
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

        check_one_author(report, keyname, firstname, suffix, author)
    # end for author in parsed_authors

    return report

def check_one_author(report, keyname, firstname, suffix, author):
    if firstname and suffix:
        name = f"{firstname} {keyname} {suffix}"
    elif firstname:
        name = f"{firstname} {keyname}"
    elif suffix:
        name = f"{keyname} {suffix}"
    else:
        name = keyname
    #
    # Some quick special cases to skip:
    if keyname.lower() == "author" and firstname == "" and suffix == "":
        return
    if keyname.lower() == "authors" and firstname == "" and suffix == "":
        return
    if keyname == ":" and firstname == "" and suffix == "":
        return
    # This is wrong
    # if suffix.lower() == "collaboration":
    #     return                  # ???
    if firstname == "":
        print( author )
        if re.search(r"collaboration", name, re.IGNORECASE) \
           or re.search(r"collaborative", name, re.IGNORECASE) \
           or re.search(r"project", name, re.IGNORECASE) \
           or re.search(r"group", name, re.IGNORECASE) \
           or re.search(r"team", name, re.IGNORECASE) \
           or re.search(r"belle", name, re.IGNORECASE):
            pass
        else:
            report.add_complaint( WARN, "Authors: lone surname", name)
        #
    #
    # Don't reject Sylvie ROUX nor S ROUX
    if re.match("^[A-Z]{3,}$", keyname) and \
       re.match("^[A-Z]{3,}$", firstname):
        report.add_complaint( WARN, "Author name is in all caps", name)
    #
    if re.match(r"^[A-Z]$", keyname) or \
       re.match(r"^[A-Z]\.$", keyname):
        report.add_complaint( WARN, "Author: found initial not surname", name)
    #
    # Reject e. e. cummings and "evans". Don't reject J von
    if keyname == keyname.lower() and \
       (firstname is None or firstname == firstname.lower()):
        report.add_complaint( WARN, "Authors: no caps in name", name)
    #
    if re.search(r"\[|]", keyname) or \
       re.search(r"\[|]", firstname) or \
       re.search(r"\[|]", suffix):
        report.add_complaint( WARN, "Authors: name should not contain brackets", name)
    #
    if re.search("[0-9]", keyname) or \
       re.search("[0-9]", firstname) or \
       re.search("[0-9]", suffix):
        report.add_complaint( WARN, "Authors: name should not contain digits", name)
    #
    # match A. and A.B. but not AB (or RS), Jr, Sr, III, etc.
    # This may be broken due to the rest of the author name parser
    # if re.match(r"^II|III|IV|V|VI|VII|VIII$", suffix):
    #     pass
    if re.match(r"^[A-Z]\.$", suffix) or \
       re.match(r"^[A-Z]\.[A-Z]\.$", suffix) or \
       re.match(r"^[A-Z]\.[A-Z]\.[A-Z]\.$", suffix):
        report.add_complaint( WARN, "Authors: name suffix should not contain initials", name)
    #
    for badmessage, badpattern in (
            (";", ";"),
            ("IEEE", r"\bIEEE\b"),
            ("PhD", r"\bphd\b"),
            ("prof", r"\bprof\b"),
            ("dr", r"\bdr\b"),
            ("Physics", r"\bPhysics\b"),
            ("Math", r"\bMath\b"),
            ("Inst", r"\bInst\b"),
            ("Institute", r"\bInstitute\b"),
            ("Dept", r"\bDept\b"),
            ("Department", r"\bDepartment\b"),
            ("Univ", r"\bUniv\b"),
            ("University", r"\bUniversity\b"),
            ("chatgpt", r"\bchatgpt?\b"),
            # ("llama", r"\bllama\b"),
            # ("gemini", r"\bgemini\b"),
            ("GPT-3.5", r"\bGPT-3.5\b"),
            # ("GPT-4", r"\bGPT-4\b"),
            ("GPT-4", r"\bGPT-4"), # Also match 4o, etc
            ("PaLM2", r"\bPalM2\b"),
            # Claude and Bert are too common
    ):
        if re.search(badpattern, keyname, re.IGNORECASE) or \
           re.search(badpattern, firstname, re.IGNORECASE) or \
           re.search(badpattern, suffix, re.IGNORECASE):
            print( keyname, firstname, suffix )
            report.add_complaint( WARN, f"Authors: name should not contain {badmessage}", name)
        #
    # end for badword in badwords

    for badword in ("Llama", "Olamma", "Gemini", "Bert", "Bart"):
        if badword.lower() == keyname.lower() and firstname == "" and suffix == "":
            report.add_complaint( WARN, f"Authors: name should not contain {badword}", name)
        #
    #

    return

def check_abstract(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if v is None or v == "":
        report.add_complaint( HOLD, "Abstract cannot be empty")
    elif len(v) < MIN_ABSTRACT_LEN:
        report.add_complaint( WARN, "Abstract: too short")
    #
    if re.match( r"abstract\b", v, re.IGNORECASE):
        report.add_complaint( WARN, "Abstract: begins with 'abstract'")
    #
    if re.search( r"\\\\", v):
        report.add_complaint( WARN, "Abstract: contains line break")
    #
    if looks_like_all_caps(v):
        report.add_complaint( WARN, "Abstract: excessive capitalization")
    # elif long_word_caps(v):
    #     report.add_complaint( WARN, "Abstract: excessive capitalization (words)")
    #
    # JHY : this is not very smart
    if smart_starts_with_lowercase_check(v):
        report.add_complaint( WARN, "Abstract: starts with a lower case letter")
    #
    if re.search( r"\\href{", v):
        report.add_complaint( WARN, "Abstract: contains \\href")
    #
    if re.search( r"\\url{", v):
        report.add_complaint( WARN, "Abstract: contains \\url")
    #
    if contains_outside_math( r"\\emph", v):
        report.add_complaint( WARN, "Abstract: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        report.add_complaint( WARN, "Abstract: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        report.add_complaint( WARN, "Abstract: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        report.add_complaint( WARN, "Abstract: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        report.add_complaint( WARN, "Abstract: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        report.add_complaint( WARN, "Abstract: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        report.add_complaint( WARN, "Abstract: contains unnecessary escape: \\%")
    #
    if contains_html_elements(v):
        report.add_complaint( WARN, "Abstract: contains HTML")
    #
    if not all_brackets_balanced(v):
        report.add_complaint( WARN, "Abstract: unbalanced brackets")
    #
    # JHY: \begin{equation}, etc are permitted ...
    if re.search( r"\\begin[^{]", v):
        report.add_complaint( WARN, "Abstract contains \\begin")
    #
    if language_is_not_english(v):
        report.add_complaint( WARN, "Abstract does not appear to be English")
    #
    # not implemented: abstract MAY end in punctuation
    # not implemented: check for arXiv or arXiv:ID
    return report

def check_comments(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    # Empty comments are ok!
    if re.search( r"\\\\", v):
        report.add_complaint( WARN, "Comments: contains line break")
    #
    if looks_like_all_caps(v):
        report.add_complaint( WARN, "Comments: excessive capitalization")
    #
    if re.search( r"\\href{", v):
        report.add_complaint( WARN, "Comments: contains \\href")
    #
    if re.search( r"\\url{", v):
        report.add_complaint( WARN, "Comments: contains \\url")
    #
    if contains_outside_math( r"\\emph", v):
        report.add_complaint( WARN, "Comments: contains \\emph")
    #
    if contains_outside_math( r"\\uline", v):
        report.add_complaint( WARN, "Comments: contains \\uline")
    #
    if contains_outside_math( r"\\textbf", v):
        report.add_complaint( WARN, "Comments: contains \\textbf")
    #
    if contains_outside_math( r"\\texttt", v):
        report.add_complaint( WARN, "Comments: contains \\texttt")
    #
    if contains_outside_math( r"\\textsc", v):
        report.add_complaint( WARN, "Comments: contains \\textsc")
    #
    if contains_outside_math( r"\\#", v):
        report.add_complaint( WARN, "Comments: contains unnecessary escape: \\#")
    #
    if contains_outside_math( r"\\%", v):
        report.add_complaint( WARN, "Comments: contains unnecessary escape: \\%")
    #
    if not all_brackets_balanced(v):
        report.add_complaint( WARN, "Comments: unbalanced brackets")
    #
    if contains_bad_encoding(v):
        report.add_complaint( WARN, "Comments: bad unicode encoding")
    #
    # TODO: check that language is English?
    return report

def check_report_num(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_REPORT_NUM_LEN:
        report.add_complaint( HOLD, "Report-no: too short" )
    elif re.match(r"^[0-9]*$", v):
        report.add_complaint( HOLD, "Report-no: no letters" )
    elif re.match(r"^[A-Za-z-]*$", v):
        report.add_complaint( HOLD, "Report-no: no digits" )
    return report

def check_journal_ref(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_JOURNAL_REF_LEN:
        report.add_complaint( WARN,  "jref: too short" )
    #
    # TODO: check for author name(s) in jref
    # TODO: check for paper title in jref
    if re.search( "http:", v, re.IGNORECASE ) or \
       re.search( "https:", v, re.IGNORECASE ):
        report.add_complaint( WARN,  "jref: contains URL" )
    #
    if re.search( "doi", v, re.IGNORECASE ):
        report.add_complaint( WARN,  "jref: contains DOI" )
    #
    if re.search( "accepted", v, re.IGNORECASE ):
        report.add_complaint( WARN,  "jref: contains 'accepted'" )
    #
    if re.search( "submitted", v, re.IGNORECASE ):
        report.add_complaint( WARN,  "jref: contains 'submitted'" )
    #
    if not re.search( "[12][90][0-9][0-9]", v ):
        report.add_complaint( WARN,  "jref: missing year" )
    #
    if re.search( "inproceedings", v, re.IGNORECASE ) or \
       re.search( "title=", v, re.IGNORECASE ) or \
       re.search( "booktitle=", v, re.IGNORECASE ): # redundant
        report.add_complaint( WARN,  "jref: copy from bibtex" )
    #
    # TODO: "validate input encoding" - what does this mean?
    return report

def check_doi(v: str) -> MetadataCheckReport:
    report = MetadataCheckReport()
    if len(v) < MIN_DOI_LEN:
        report.add_complaint( WARN, "doi: too short" )
    if re.search( "http:", v ):
        report.add_complaint( WARN, "doi: contains http:" )
    if re.search( "https:", v ):
        report.add_complaint( WARN, "doi: contains https:" )
    if re.search( "doi:", v ):
        report.add_complaint( WARN, "doi: contains doi:" )
    # Is this right?
    if re.search( "arxiv-doi", v ):
        report.add_complaint( WARN, "doi: contains arxiv-doi" )
    return report

