"""Generic checks package: exposes all generic checks."""

from qa.checks.generic.length import (  # noqa
    NotTooLong,
    NotTooShort,
)

from qa.checks.generic.acm_class import (  # noqa
    AcmClassHasValidFormat,
)

from qa.checks.generic.whitespace import (  # noqa
    DoesNotContainSpaceBeforeComma,
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
    NoUtf8DecodingErrors,
)

from qa.checks.generic.structure import (  # noqa
    AllBracketsBalanced,
    DoesNotContainAnnotationSymbols,
    DoesNotContainHtmlEscapes,
    DoesNotContainUnacceptableHtmlTags,
    NoHtmlElements,
)

from qa.checks.generic.tex import (  # noqa
    DoesNotContainBibtex,
    DoesNotContainHrefOrUrlTex,
    DoesNotContainLinebreak,
    DoesNotContainTexBegin,
    DoesNotContainTexDagger,
    DoesNotContainUnnecessaryEscape,
)

from qa.checks.generic.punctuation import (  # noqa
    DoesNotContainComma,
    DoesNotContainSemicolon,
    DoesNotEndWithPunctuation,
)

from qa.checks.generic.doi import (  # noqa
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
    DoesNotContainEtAl,
    DoesNotContainPendingPublicationStatus,
    DoesNotContainSubmitted,
    DoesNotContainUrl,
    IsEnglish,
)

from qa.checks.generic.presence import (  # noqa
    EmptyFieldCheck,
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
