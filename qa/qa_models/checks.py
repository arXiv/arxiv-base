
from enum import Enum

from arxiv.metadata import (
    FieldName,
    Complaint,
)

class Check(Enum):
    # Old id for all overlaps
    OVERLAP = 6
    # Use this for all flagged terms in one message
    FLAGGED_TERMS = 7
    CONCERNING_WORDS = 7        # old term
    MISSING_AUTHOR = 8
    WITHDRAWAL = 9
    RATE_LIMITED_NEW = 10
    FIRST_SUBMISSION = 11
    LOW_QUALITY = 12
    NONSTANDARD_FORMAT = 13
    MISSING_TEXT = 14
    SHORT_TEXT = 15
    UNKNOWN_LANGUAGE = 16
    LOW_PERCENT_ENGLISH = 17
    MISSING_REFERENCES = 18
    MISSING_BIBLIOGRAPHY = 19
    TOO_MANY_PAGES = 20
    FLAGGED_PUBLISHED_ONLY = 21
    FLAGGED_PREVIOUS_OUT_OF_SCOPE = 22
    FLAGGED_PREVIOUS_LOW_QUALITY = 23
    FLAGGED_SUBMITTER = 24
    GENERAL_CATEGORY_WITH_CROSSES = 25
    UNDERGRADUATE_WORK = 26
    MASTERS_THESIS = 27
    NO_PRIMARY_CATEGORY = 28
    OUT_OF_SCOPE = 29
    PROXY_AUTHORS_MISSING_SUBMITTER = 30
    PROXY_UNAUTHORIZED = 31
    PROXY_MISSING_IN_AUTHORS = 32
    LINE_NUMBERS = 33
    AUTHORS_MISSING_IN_TEXT = 34
    CHECK_AUTHORS = 35
    OVERLAP_DUPLICATE_TEXT = 36
    OVERLAP_WRONG_REPLACEMENT = 37
    OVERLAP_REPLACEMENT = 38
    MODERATE_OVERLAP_SAME_AUTHORS = 39
    HIGH_OVERLAP_DIFFERENT_AUTHORS = 40
    MODERATE_OVERLAP_DIFFERENT_AUTHORS = 41
    BAD_CATEGORY = 42           # ?
    RATE_LIMITED_REPLACEMENT = 43
    JAVASCRIPT_IN_PDF = 44
    PDF_NEEDS_TEX = 45
    PDFPAGES = 46
    OBFUSCATED_TEX = 47
    OVERSIZE_FILES = 48
    OVERSIZE_IMAGES = 49
    HTML_SUBMISSION = 50
    GENERAL_CATEGORY = 51       # from non-flagged submitter
    GENERAL_CATEGORY_AS_CROSS = 52
    NONSTANDARD_ARTICLE_TYPE = 53

    # Checks >= 100, < 1000 are metadata checks
    # There is room here for (field x complaint) if we want to get more granular
    METADATA_TITLE = 100
    METADATA_AUTHORS = 200
    METADATA_ABSTRACT = 300
    METADATA_COMMENTS = 400
    METADATA_REPORT_NUM = 500
    METADATA_JOURNAL_REF = 600
    METADATA_DOI = 700
    METADATA_ACM_CLASS = 800
    METADATA_MSC_CLASS = 900
    
    # checks > 1000 are checks due to flagged terms (fka concerning words) 
    FLAGGED_TERMS_OFFSET = 1000



def check_to_check_id(check: Check) -> int:
    return check.value


fieldname2check = {
    FieldName.TITLE: Check.METADATA_TITLE,
    FieldName.AUTHORS: Check.METADATA_AUTHORS,
    FieldName.ABSTRACT: Check.METADATA_ABSTRACT,
    FieldName.COMMENTS: Check.METADATA_COMMENTS,
    FieldName.REPORT_NUM: Check.METADATA_REPORT_NUM,
    FieldName.JOURNAL_REF: Check.METADATA_JOURNAL_REF,
    FieldName.DOI: Check.METADATA_DOI,
    FieldName.ACM_CLASS: Check.METADATA_ACM_CLASS,
    FieldName.MSC_CLASS: Check.METADATA_MSC_CLASS
}
    
def fieldname_to_check(fieldname: FieldName) -> Check:
    return fieldname2check[fieldname]
    
def metadata_check_to_check_id(fieldname: FieldName, complaint: Complaint) -> int:
    return check_to_check_id(fieldname2check[fieldname]) + complaint.value

def flagged_term_to_check_id(flagged_term_id: int) -> int:
    return check_to_check_id(Check.FLAGGED_TERMS_OFFSET) + flagged_term_id




    
