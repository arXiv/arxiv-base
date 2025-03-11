
# placeholder

from enum import StrEnum

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

class Disposition(StrEnum):
    OK = "ok"
    WARN = "warn"
    HOLD = "hold"

