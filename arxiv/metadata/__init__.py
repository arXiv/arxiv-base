
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
    SOURCE_TYPE = "source_type"
    COMMENTS = "comments"
    REPORT_NUM = "report_num"
    JOURNAL_REF = "journal_ref"
    DOI = "doi"

class Disposition(StrEnum):
    OK = "ok"
    WARN = "warn"
    HOLD = "hold"

