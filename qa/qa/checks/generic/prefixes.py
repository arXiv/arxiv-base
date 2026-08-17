"""Generic field-prefix checks."""

from qa.checks.base import BaseGenericPatternCheck


class DoesNotBeginWithTitle(BaseGenericPatternCheck):
    name = "does_not_begin_with_title"
    display_name = "Does Not Begin With Title"
    id = 10003
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'title:'."
    failure_message = "Begins with 'title'."

    _pattern = r"(?i)^title:?\b"


class DoesNotBeginWithAuthor(BaseGenericPatternCheck):
    name = "does_not_begin_with_author"
    display_name = "Does Not Begin With Author"
    id = 10004
    version = "1.0.0"
    description = "The value does not begin with the prefix 'author' or 'authors'."
    failure_message = "Begins with 'author'."

    _pattern = r"(?i)^authors?:?\b"


class DoesNotBeginWithAbstract(BaseGenericPatternCheck):
    name = "does_not_begin_with_abstract"
    display_name = "Does Not Begin With Abstract"
    id = 10005
    version = "1.0.0"
    description = "The value does not begin with the literal prefix 'abstract' or 'abstract:'."
    failure_message = "Begins with 'abstract'."

    _pattern = r"(?i)^abstract:?\b"


class DoesNotBeginWithDoiPrefix(BaseGenericPatternCheck):
    name = "does_not_begin_with_doi_prefix"
    display_name = "Does Not Begin With DOI Prefix"
    id = 10047
    version = "1.0.0"
    description = "The value does not begin with 'doi:', 'https://doi.org/', or similar URL prefixes."
    failure_message = "Begins with an unnecessary DOI prefix: 'doi:' or 'https://doi.org/'."

    _pattern = r"(?i)^doi:|^https?://doi\.org/|^https?://.*\.doi\.org/"
