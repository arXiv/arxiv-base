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
    CANNOT_BE_EMPTY = 1
    TOO_SHORT = 2
    CONTAINS_BAD_STRING = 3
    EXCESSIVE_CAPITALIZATION = 4
    UNBALANCED_BRACKETS = 5
    BAD_UNICODE = 6
    CONTAINS_LONE_SURNAME = 7
    CONTAINS_INITIALS = 8
    NO_CAPS_IN_NAME = 9
    MUST_CONTAIN_LETTERS = 10
    MUST_CONTAIN_DIGITS = 11
    MUST_CONTAIN_YEAR = 12
    MUST_BE_ENGLISH = 13
    TOO_LONG = 14
