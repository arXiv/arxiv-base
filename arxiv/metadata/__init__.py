# placeholder

from enum import StrEnum
from enum import IntEnum


class Color(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class FieldName(StrEnum):
    TITLE = "title"
    AUTHORS = "authors"
    ABSTRACT = "abstract"
    # source_type is internal, not checked
    COMMENTS = "comments"
    REPORT_NUM = "report_num"
    JOURNAL_REF = "journal_ref"
    DOI = "doi"
    MSC_CLASS = "msc_class"


class Disposition(StrEnum):
    OK = "ok"
    WARN = "warn"
    HOLD = "hold"


class Complaint(IntEnum):
    """These complaints are also listed in the arxiv_checks table -
    once per field - plus in this Confluence document: https://arxiv-org.atlassian.net/wiki/spaces/AD/database/1733853212

    """
    CANNOT_BE_EMPTY = 1
    TOO_SHORT = 2
    BEGINS_WITH_TITLE = 3
    BEGINS_WITH_AUTHOR = 4
    BEGINS_WITH_ABSTRACT = 5
    CONTAINS_LINEBREAK = 6
    EXCESSIVE_CAPITALIZATION = 7
    BEGINS_WITH_LOWERCASE = 8
    CONTAINS_TEX = 9            # post-MVP
    # \% and other TeX-isms?
    UNNECESSARY_ESCAPE = 10
    CONTAINS_HTML = 11
    # ? 12 ?
    UNBALANCED_BRACKETS = 13
    BAD_UNICODE_ENCODING = 14
    BAD_CHARACTER = 15
    LEADING_WHITESPACE = 16
    TRAILING_WHITESPACE = 17
    WHITESPACE_BEFORE_COMMA = 18
    CONTAINS_ANONYMOUS = 19
    CONTAINS_CORRESPONDING = 20
    CONTAINS_DAGGER = 21
    CONTAINS_SEMICOLON = 22
    CONTAINS_LONE_SURNAME = 23
    # CONTAINS_INITIALS - Under consideration: surname or suffix contains initials
    CONTAINS_AFFILIATION = 24 # Contains something like "department" or "University"
    # ? ends with a period ? 
    EXTRA_WHITESPACE = 25       # multiple spaces/tabs
    CONTAINS_CONTROL_CHARS = 26
    CONTAINS_CONTROL_CHARS_ABS = 27 # does not include newlines
    # Missing: 28
    # Under consideration:
    # ET_AL_PUNCTUATION
    # NAME_IN_ALL_CAPS
    # CONTAINS_INITIALS
    TRAILING_PUNCTUATION = 29
    CONTAINS_NUMBER = 30
    # "TeX accent with intervening space
    BAD_TEX_ACCENT = 31
    TILDE_AS_HARD_SPACE = 32
    UNNECESSARY_SPACE_IN_PARENS = 33
    MUST_BE_ENGLISH = 34
    # PARAGRAPHS cannot begin or end with whitespace
    EXTRA_WHITESPACE_ABS = 35
    TOO_LONG = 36
    MUST_CONTAIN_DIGITS = 37
    MUST_CONTAIN_LETTERS = 38
    CONTAINS_URL = 39
    CONTAINS_DOI = 40
    CONTAINS_ACCEPTED = 41
    CONTAINS_SUBMITTED = 42
    MUST_CONTAIN_YEAR = 43
    CONTAINS_BIBTEX = 44
    # Contains the string "DOI"
    CONTAINS_DOI2 = 45
    CONTAINS_ARXIV_DOI = 46
    BAD_DOI_PREFIX = 47
    INSUFFICIENT_ALPHA = 48
    LLM_AUTHOR_DETECTED = 49
    INVALID_DOI = 50
