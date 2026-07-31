"""Author metadata checks."""

import re
from arxiv.authors import parse_author_affil

from qa.checks.base import BaseCheck, BaseAggregateCheck, EmptyFieldError
from qa.checks.models import QaDataRegistry, OnFailurePolicy, Metadata, Result
from qa.checks.generic.text import (
    AllBracketsBalanced,
    DoesNotBeginWithAuthor,
    DoesNotContainAnonymous,
    DoesNotContainCorresponding,
    DoesNotContainControlChars,
    DoesNotContainLinebreak,
    DoesNotContainTexDagger,
    DoesNotContainTildeAsHardSpace,
    DoesNotEndWithPunctuation,
    NoAnnotationSymbols,
    NoBoundaryWhitespace,
    NoExtraWhitespace,
    NoHtmlElements,
    NoUnnecessarySpaceInParens,
    NoUtf8DecodingErrors,
    NotTooLong,
    NotTooShort,
)
from qa.checks.generic.author_name import (
    AuthorNamesDoNotContainAffiliation,
    AuthorNamesDoNotContainBrackets,
    AuthorNamesDoNotContainNumbers,
    AuthorNamesDoNotContainSemicolon,
    AuthorsDoNotContainLlmAuthor,
    AuthorsDoNotContainLoneSurname,
)


class AuthorsAreValid(BaseAggregateCheck):
    """Aggregate check for the metadata authors field."""

    name = "authors_are_valid"
    display_name = "Authors Are Valid"
    id = 200
    version = "1.0.0"
    description = "The metadata authors field is valid."
    on_failure_policy = OnFailurePolicy.REJECT
    failure_message = "Authors are invalid or empty."

    required_data = {"metadata"}

    @classmethod
    def check(cls, authors: str | None) -> Result:
        return cls().run(QaDataRegistry(metadata=Metadata(authors=authors)))

    _checks = (
        NotTooShort(4, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NotTooLong(10000, on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainLinebreak(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoAnnotationSymbols(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoBoundaryWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoExtraWhitespace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainAnonymous(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainCorresponding(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainTexDagger(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotBeginWithAuthor(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoHtmlElements(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AllBracketsBalanced(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoUnnecessarySpaceInParens(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainTildeAsHardSpace(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotEndWithPunctuation(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        DoesNotContainControlChars(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        NoUtf8DecodingErrors(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLoneSurname(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorsDoNotContainLlmAuthor(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainSemicolon(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainBrackets(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainNumbers(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
        AuthorNamesDoNotContainAffiliation(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="authors"),
    )

def normalize_author_name(name: str):
    name = name.replace("\u00a0", " ") # non-breaking space
    name = name.replace(".", " ")
    name = name.replace(",", " ")        
    name = name.replace("-", " ")        
    name = name.replace("\u2010", " ") # "True hyphen"
    name = name.replace("\u2011", " ") # "Non-breaking hyphen"
    name = name.replace("  ", " ")
    return name.lower()
    
def is_name1_contained_in_name2(name1s: list[str], name2s: list[str]):
    # name1 is "conteined" in name2 if any of the names in name1 are
    # found in name2, and either all names are found, or one of the names is long enough
    
    # we assume that name1 and name2 have been normalized and split() here

    all_short_name1_names_found = True
    all_name1_names_short = True
    any_long_name1_found = False

    for name1name in name1s:
        if len(name1name) <= 2:
            # short
            if name1name in name2s:
                pass
            else:
                all_short_name1_names_found = False
        else:
            all_name1_names_short = False
            if name1name in name2s:
                any_long_name1_found = True
                break

    return (any_long_name1_found or
            (all_name1_names_short and all_short_name1_names_found))

known_collaborations = [
    r"ATLAS Collaboration",
    r"CMS Collaboration",
    r"ATLAS and CMS Collaborations",
    r"CMS and TOTEM Collaborations",
    # "Tracker Group of the CMS Collaboration",
    r"ALICE Collaboration",
    r"STAR Collaboration",
    r"LHCb collaboration"
    r"Belle Collaboration",
]


def known_collaboration(authors: str):
    """These collaborations are exempt from the requirement that the
    authors list include the submitter name.
    """
    for c in known_collaborations:
        if re.search(c, authors, flags=re.IGNORECASE):
            return True
    return False


class AuthorsContainsSubmitterName(BaseCheck):
    name = "authors_contains_submitter_name"
    display_name = "Authors Contains Submitter Name"
    id = 30
    version = "1.0.0"
    description = "Submitter name found in authors field."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Submitter name not found in authors field (proxy check)."

    required_data = {"metadata", "submit_event_info"}

    failure_flag_id = "submitter-name-not-found-in-authors-field"

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "failure_flag_id": self.failure_flag_id,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        if data_registry.metadata is None:
            raise EmptyFieldError("Field metdata is empty.")
        if data_registry.submit_event_info is None:
            raise EmptyFieldError("Field submit_event_info is empty.")
            
        authors = data_registry.metadata.authors
        
        submitter_name = data_registry.submit_event_info.submitter_name
        submitter_names = normalize_author_name(submitter_name).split()

        passed = False

        if authors is None:
            return self._result(passed=True)

        if known_collaboration(authors):
            return self._result(passed=True)
        
        parsed_authors = parse_author_affil(authors)

        if len(parsed_authors) > 50:
            return self._result(passed=True)
        
        for author in parsed_authors:
            keyname, firstname, suffix, *_ = author
            author_names = normalize_author_name(f"{firstname} {keyname}").split()
            if is_name1_contained_in_name2(submitter_names, author_names):
                passed = True
                break

        if passed:
            return self._result(passed=True)
        else:
            return self._result(passed=False, message=self.failure_message)
