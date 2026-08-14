"""Generic checks package: exposes all generic checks."""

from qa.checks.generic.length import (  # noqa
    NotTooLong,
    NotTooShort,
)

from qa.checks.generic.whitespace import (  # noqa
    DoesNotContainSpaceAfterOpenParen,
    DoesNotContainSpaceBeforeComma,
    DoesNotContainUnspacedComma,
    NoExtraWhitespace,
    NoUnnecessarySpaceInParens,
)

from qa.checks.generic.casing import (  # noqa
    DoesNotStartWithLowercase,
    NoExcessiveCapitals,
    NotAllCaps,
)

from qa.checks.generic.encoding import (  # noqa
    DoesNotContainControlChars,
    DoesNotContainControlCharsAllowNewlines,
    DoesNotContainRawNewline,
    NoUtf8DecodingErrors,
)

from qa.checks.generic.structure import (  # noqa
    AllBracketsBalanced,
    NoHtmlElements,
)

from qa.checks.generic.tex import (  # noqa
    DoesNotContainBibtex,
    DoesNotContainHrefOrUrlTex,
    DoesNotContainLinebreak,
    DoesNotContainTexBegin,
    DoesNotContainTexDagger,
    DoesNotContainTildeAsHardSpace,
    DoesNotContainUnnecessaryEscape,
)

from qa.checks.generic.prefixes import (  # noqa
    DoesNotBeginWithAbstract,
    DoesNotBeginWithAuthor,
    DoesNotBeginWithDoiPrefix,
    DoesNotBeginWithTitle,
)

from qa.checks.generic.punctuation import (  # noqa
    DoesNotContainSemicolon,
    DoesNotEndWithPeriod,
    DoesNotEndWithPunctuation,
)

from qa.checks.generic.doi_url import (  # noqa
    DoiHasValidFormat,
)

from qa.checks.generic.content import (  # noqa
    ContainsALetterAndADigit,
    ContainsAValidYear,
    DoesNotContainAccepted,
    DoesNotContainAnonymous,
    DoesNotContainBareDoi,
    DoesNotContainCorresponding,
    DoesNotContainDoi,
    DoesNotContainEtAlWithPeriod,
    DoesNotContainPendingPublicationStatus,
    DoesNotContainSubmitted,
    DoesNotContainUrl,
    NoAnnotationSymbols,
)

from qa.checks.generic.author_name import (  # noqa
    AuthorNamesDoNotContainAffiliation,
    AuthorNamesDoNotContainBrackets,
    AuthorNamesDoNotContainDegreeSuffix,
    AuthorNamesDoNotContainNumbers,
    AuthorNamesDoNotContainPrefix,
    AuthorNamesDoNotContainSemicolon,
    AuthorsDoNotContainLlmAuthor,
    AuthorsDoNotContainLoneSurname,
)
