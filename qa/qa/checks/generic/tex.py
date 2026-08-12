"""Generic TeX/LaTeX checks."""

from qa.checks.base import BaseGenericPatternCheck


class DoesNotContainLinebreak(BaseGenericPatternCheck):
    name = "does_not_contain_linebreak"
    display_name = "Does Not Contain Linebreak"
    id = 10006
    version = "1.0.0"
    description = "The value does not contain LaTeX-style or escaped linebreaks."
    failure_message = "Contains a line break."

    _pattern = r"(?i)\\\\"


class DoesNotContainUnnecessaryEscape(BaseGenericPatternCheck):
    name = "does_not_contain_unnecessary_escape"
    display_name = "Does Not Contain Unnecessary Escape"
    id = 10010
    version = "1.0.0"
    description = "The value does not contain unnecessary escape characters preceding #, %, $, or _ symbols."
    failure_message = "Contains unnecessary escape."

    _pattern = r"\\#|\\%|\\\$|\\_"


class DoesNotContainHrefOrUrlTex(BaseGenericPatternCheck):
    name = "does_not_contain_href_or_url_tex"
    display_name = "Does Not Contain Href Or Url TeX"
    id = 10009
    version = "1.0.0"
    description = "The value does not contain href or url raw TeX commands."
    failure_message = "Contains href or url TeX."

    _pattern = r"(?i)\\href\{|\\url\{"


class DoesNotContainBibtex(BaseGenericPatternCheck):
    name = "does_not_contain_bibtex"
    display_name = "Does Not Contain BibTeX"
    id = 10044
    version = "1.0.0"
    description = "The value does not contain BibTeX field assignments."
    failure_message = "Contains bibtex."

    _pattern = r"(?i)(title|booktitle|inproceedings)="


class DoesNotContainTexBegin(BaseGenericPatternCheck):
    name = "does_not_contain_tex_begin"
    display_name = "Does Not Contain TeX Begin"
    id = 10017
    version = "1.0.0"
    description = "The value does not contain a tex begin command that is not followed by a curly brace."
    failure_message = "Contains TeX."

    _pattern = r"(?i)\\begin[^{]"


class DoesNotContainTexDagger(BaseGenericPatternCheck):
    name = "does_not_contain_tex_dagger"
    display_name = "Does Not Contain TeX Dagger"
    id = 10021
    version = "1.0.0"
    description = "The value does not contain TeX dagger symbols (\\dag, \\ddag, etc.)."
    failure_message = "Contains a dagger symbol."

    _pattern = r"\\dag|\\ddag|\\textdag|\\textddag"


class DoesNotContainTildeAsHardSpace(BaseGenericPatternCheck):
    name = "does_not_contain_tilde_as_hard_space"
    display_name = "Does Not Contain Tilde As Hard Space"
    id = 10032
    version = "1.0.0"
    description = "The value does not contain an unescaped tilde used as a hard space."
    failure_message = "Tilde as hard space."

    _pattern = r"[^\\]~"
