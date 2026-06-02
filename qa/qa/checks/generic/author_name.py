"""Generic author name checks."""

import re
from abc import abstractmethod

from arxiv.authors import parse_author_affil

from qa.checks.base import BaseGenericCheck
from qa.checks.models import Inputs, Disposition, Result


_LLM_STANDALONE_NAMES = frozenset([
    "llama", "olamma", "gemini", "claude", "bert", "bart", "grok",
    "chatgpt", "gpt-3", "gpt-3.", "gpt-4", "gpt-4.", "gpt-5", "gpt-5.", "palm2",
])


def _build_name(keyname: str, firstname: str, suffix: str) -> str:
    if suffix:
        return f"{firstname} {keyname} {suffix}" if firstname else f"{keyname} {suffix}"
    return f"{firstname} {keyname}" if firstname else keyname


class BaseAuthorCheck(BaseGenericCheck):
    """A check that parses authors and validates individual author entries."""

    @abstractmethod
    def _check_author(self, keyname: str, firstname: str, suffix: str) -> bool:
        """Return True if the author passes, False if it fails."""
        ...

    def _run(self, inputs: Inputs) -> Result:
        v = getattr(getattr(inputs, self.data), self.field)
        for author in parse_author_affil(v):
            keyname, firstname, suffix, *_ = author
            if not self._check_author(keyname, firstname, suffix):
                return self._result(passed=False, message=self.failure_message)
        return self._result(passed=True)


class BaseAuthorPatternCheck(BaseAuthorCheck):
    """An author check that applies a regex pattern (matches are failing)."""

    _pattern: str

    def __init__(self, *, disposition: Disposition, data: str, field: str) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self._compiled_pattern = re.compile(self._pattern)

    @property
    def config(self) -> dict:
        return {**super().config, "pattern": self._pattern}

    def _check_author(self, keyname: str, firstname: str, suffix: str) -> bool:
        return not (
            self._compiled_pattern.search(keyname)
            or self._compiled_pattern.search(firstname)
            or self._compiled_pattern.search(suffix)
        )


class AuthorsDoNotContainLoneSurname(BaseAuthorCheck):
    name = "authors_do_not_contain_lone_surname"
    id = 23
    version = "1.0.0"
    description = "No author has only a surname without a given name, unless it is a known collaboration or LLM name."
    failure_message = "Contains lone surname"

    _collaboration_patterns = [
        r"collaboration",
        r"collaborative",
        r"project",
        r"group",
        r"team",
        r"belle",
    ]

    _pattern = "|".join(_collaboration_patterns)

    def __init__(self, *, disposition: Disposition, data: str, field: str) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self._compiled_pattern = re.compile(self._pattern, re.IGNORECASE)

    @property
    def config(self) -> dict:
        return {**super().config, "collaboration_patterns": self._collaboration_patterns}

    def _check_author(self, keyname: str, firstname: str, suffix: str) -> bool:
        if firstname != "":
            return True
        if self._compiled_pattern.search(keyname):
            return True
        if keyname.lower() in _LLM_STANDALONE_NAMES:
            return True
        return False


class AuthorsDoNotContainLlmAuthor(BaseAuthorCheck):
    name = "authors_do_not_contain_llm_author"
    id = 49
    version = "1.0.0"
    description = "No author's name appears to be an AI language model."
    failure_message = "Potential LLM author detected."

    _llm_name_patterns = [
        r"\bchatgpt?\b",
        r"\bGPT-4",
        r"\bGPT-5",
        r"\bGPT-3\.",
        r"\bGPT-3\.5\b",
        r"\bGPT-4\.",
        r"\bGPT-5\.",
        r"\bPaLM2\b",
        r"\bGemini\b",
    ]

    _pattern = "|".join(_llm_name_patterns)

    def __init__(self, *, disposition: Disposition, data: str, field: str) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self._compiled_pattern = re.compile(self._pattern, re.IGNORECASE)

    @property
    def config(self) -> dict:
        return {**super().config, "pattern": self._pattern}

    def _check_author(self, keyname: str, firstname: str, suffix: str) -> bool:
        if firstname == "" and keyname.lower() in _LLM_STANDALONE_NAMES:
            return False
        return not self._compiled_pattern.search(_build_name(keyname, firstname, suffix))


class AuthorNamesDoNotContainSemicolon(BaseAuthorPatternCheck):
    name = "author_names_do_not_contain_semicolon"
    id = 22
    version = "1.0.0"
    description = "No parsed author name contains a semicolon."
    failure_message = "Contains semicolon(s) - use ',' or 'and' to separate authors."

    _pattern = r";"


class AuthorNamesDoNotContainBrackets(BaseAuthorPatternCheck):
    name = "author_names_do_not_contain_brackets"
    id = 15
    version = "1.0.0"
    description = "No parsed author name contains square bracket characters."
    failure_message = "Unusual character detected."

    _pattern = r"\[|]"


class AuthorNamesDoNotContainNumbers(BaseAuthorPatternCheck):
    name = "author_names_do_not_contain_numbers"
    id = 30
    version = "1.0.0"
    description = "No parsed author name contains numeric digits."
    failure_message = "Contains a number."

    _pattern = r"[0-9]"


class AuthorNamesDoNotContainAffiliation(BaseAuthorPatternCheck):
    name = "author_names_do_not_contain_affiliation"
    id = 24
    version = "1.0.0"
    description = "No parsed author name contains institution or affiliation keywords."
    failure_message = "Contains a suffix that may be university affiliation or degree related."

    _affiliation_patterns = [
        r"\bIEEE\b",
        r"\bphd\b",
        r"\bprof\b",
        r"\bdr\b",
        r"\bPhysics\b",
        r"\bMath\b",
        r"\bInst\b",
        r"\bInstitute\b",
        r"\bDept\b",
        r"\bDepartment\b",
        r"\bUniv\b",
        r"\bUniversity\b",
    ]

    _pattern = "|".join(_affiliation_patterns)

    def __init__(self, *, disposition: Disposition, data: str, field: str) -> None:
        super().__init__(disposition=disposition, data=data, field=field)
        self._compiled_pattern = re.compile(self._pattern, re.IGNORECASE)
