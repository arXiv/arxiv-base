import pytest

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


try:
    from arxiv.metadata.metacheck import combine_dispositions, Metadata
except ModuleNotFoundError:
    pytest.skip(
        """"gcld3 and/or protobuf-compile are not installed.
            To run these tests, install with:
            sudo apt install -y protobuf-compiler
            poetry install --extras qa""",
        allow_module_level=True,
    )

from arxiv.metadata import FieldName
from arxiv.metadata import Disposition
from arxiv.metadata import Complaint
from arxiv.metadata import metacheck

from arxiv.metadata.metacheck import MetadataCheckReport

from arxiv.metadata.metacheck import combine_dispositions
from arxiv.metadata.metacheck import long_word_caps

############################################################
TITLE = FieldName.TITLE
AUTHORS = FieldName.AUTHORS
ABSTRACT = FieldName.ABSTRACT
# Source type is "internal metadata"
COMMENTS = FieldName.COMMENTS
REPORT_NUM = FieldName.REPORT_NUM
JOURNAL_REF = FieldName.JOURNAL_REF
DOI = FieldName.DOI
MSC_CLASS = FieldName.MSC_CLASS

OK = Disposition.OK
WARN = Disposition.WARN
HOLD = Disposition.HOLD

############################################################
# Helper functions for unit tests


def check_result(
    result: MetadataCheckReport, expected: Optional[Tuple[Disposition, List[Complaint]]]
):
    # result should be ( OK, [] ) or (HOLD, [message, message...]) or (WARN, ...)
    if expected is None:
        if (result.get_disposition() != OK):
            print( "Not OK, complaints were:", result.get_complaints() )
        #
        assert result.get_disposition() == OK
    else:
        assert result.disposition == expected[0]
        assert set(result.get_complaints()) == set(expected[1])
        # TODO: test offsets?
        # assert list(result.get_offsets()) != None
    #


############################################################
# Tests for internal (helper) function combine_dispositions


def test_combine_dispositions():
    assert HOLD == combine_dispositions(HOLD, HOLD)
    assert HOLD == combine_dispositions(HOLD, WARN)
    assert HOLD == combine_dispositions(WARN, HOLD)
    assert HOLD == combine_dispositions(HOLD, OK)
    assert HOLD == combine_dispositions(OK, HOLD)
    assert WARN == combine_dispositions(WARN, WARN)
    assert WARN == combine_dispositions(WARN, OK)
    assert WARN == combine_dispositions(OK, WARN)
    assert OK == combine_dispositions(OK, OK)


############################################################l
##### TITLE field checks

TITLE_TESTS = [
    ("A fine title", None),
    ("Another title about CERN and ALPEH where z~1/2", None),
    # ("", (HOLD, [CANNOT_BE_EMPTY])),
    ("Tiny", (WARN, [Complaint.TOO_SHORT])),
    ("a title with lowercase",
     (WARN, [Complaint.BEGINS_WITH_LOWERCASE])),
    # Fewer than 0.25% of all papers start with a lower-case letter,
    # but there are some patterns, which we are not checking for:
    ("aTITLE: Not So Lowercase",
     (WARN, [Complaint.BEGINS_WITH_LOWERCASE])),
    ("  A title with leading space",
     (WARN, [Complaint.LEADING_WHITESPACE])),
    ("A title with trailing space ",
     (WARN, [Complaint.TRAILING_WHITESPACE])),
    ("A title  with  multiple  spaces",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    # NOTE: Titles can end with punctuation.
    ("A title with period.", None),
    # NOTE: the test for excessive capitalization is fragile
    ("ALL CAPS TITLE",
     (WARN, [Complaint.EXCESSIVE_CAPITALIZATION])),
    ("NOT EVEN BORDERLINE ALL CAPS TITLE",
     (WARN, [Complaint.EXCESSIVE_CAPITALIZATION])),
    ("BORDERLINE All Caps TITLE", None),
    ("BORDERLINE ALL caps TITLE",
     (WARN, [Complaint.EXCESSIVE_CAPITALIZATION])),
    ("This is a title WITH ONE LONG WORD CAPITALIZED", None),
    (
        "This is a title WITH SOME EXTRAEXTRA LONG WORDS CAPITALIZED",
        [WARN, [Complaint.EXCESSIVE_CAPITALIZATION]],
    ),
    # Not caught !?
    ("This is a title,bad title", None),
    # [WARN, [Complaint.EXTRA_WHITESPACE]]), # TODO
    ("This is a title, , bad title",
     [WARN, [Complaint.EXTRA_WHITESPACE]]),
    ("This is a title , bad title",
     [WARN, [Complaint.EXTRA_WHITESPACE]]),
    # We allow some capitalized words
    ("The is a title with known long words capitalized AMANDA CHANDRA", None),
    # But in general, we complain if there are 2 or more capitalized words
    (
        "The is a title with unknown long words capitalized UNIQUEWORD THISISATEST",
        [WARN, [Complaint.EXCESSIVE_CAPITALIZATION]],
    ),
    # but digit strings don't count
    ("The is a title with 12345678 and 987654321 words not capitalized", None),
    # Check for *some* HTML entities
    ("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>", None),
    ("Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>",
     (WARN, [Complaint.CONTAINS_HTML])),
    ("A title with HTML<br/>linebreaks<br />there",
     (WARN, [Complaint.CONTAINS_HTML])),
    ("Title: Something",
     (WARN, [Complaint.BEGINS_WITH_TITLE])),
    ("This \\ is not a line break", None),
    # ("Don't use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something",
    #  (WARN, [Complaint.BAD_CHARACTER]),
    # ),
    ("Line break at end\\\\",
     (WARN, [Complaint.CONTAINS_LINEBREAK])),
    ("This \\ is not a line break", None),
    # Tests with parens
    ("Something about sin(x), H2(SO)4, and (Non-)Commutative operations", None),
    # 'Title: contains \\href',
    # 'Title: contains \\url',
    # 'Title: contains \\emph',
    # 'Title: contains \\uline',
    # 'Title: contains \\textbf',
    # 'Title: contains \\texttt',
    # 'Title: contains unnecessary escape: \\#',
    # 'Title: contains unnecessary escape: \\%',
]


@pytest.mark.parametrize("test", TITLE_TESTS)
def test_titles(test):
    title, expected_result = test
    # result = metacheck.check({TITLE: title})
    metadata = Metadata()
    metadata.title = title
    print( "JHY", metadata )
    result = metacheck.check(metadata)
    print(test, result, expected_result)
    check_result(result[TITLE], expected_result)


############################################################
##### Detailed tests for AUTHORS field

AUTHORS_TESTS = [
    # ('',
    #  (HOLD, [CANNOT_BE_EMPTY])),
    ("C Li", None),
    ("Li C", None),
    ("C C", (WARN, [Complaint.TOO_SHORT])),
    ("Fred Smith", None),
    ("Fred Smith, Joe Bloggs", None),
    # We don't check for ellipsis, but we do get an error because "..." isn't caps!
    # ('Fred Smith, Joe Bloggs, ...',
    #  (WARN, [Complaint."Authors: ends with punctuation"])),
    ("Fred Smith,",
     (WARN, [Complaint.TRAILING_PUNCTUATION])),
    ("Fred Smith, \\ Joe Bloggs", None),
    ("Fred Smith, \\\\ Joe Bloggs",
     (WARN, [Complaint.CONTAINS_TEX])),
    (
        "Fred Smith*, Joe Bloggs#, Bob Briggs^, Jill Camana@, and Rebecca MacInnon",
        (WARN, [Complaint.BAD_CHARACTER]),
    ),
    # "Authors: contains bad character '*'",
    # "Authors: contains bad character '#'",
    # "Authors: contains bad character '^'",
    # "Authors: contains bad character '@'",
    (" Leading Whitespace",
     (WARN, [Complaint.LEADING_WHITESPACE])),
    ("Trailing Whitespace ",
     (WARN, [Complaint.TRAILING_WHITESPACE])),
    ("Multiple  Spaces",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    ("Space Tab          Space",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    ("Jane Jones (Austen Nname",
     (WARN, [Complaint.UNBALANCED_BRACKETS])),
    # ('Fred Smith(University), Joe Bloggs',"Authors: missing spaces around parenthesis"),
    ("Martha Raddatz , Ayesha Rascoe",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    # ('Fred Smith & Joe Bloggs',"Authors: possibly inappropriate ampersand"),
    # 'Authors: no caps in name',
    # 'Authors: name should not contain digits',
    ("Person with <sup>1</sup>",
     (WARN, [Complaint.CONTAINS_HTML, Complaint.CONTAINS_NUMBER])
    ),
    ("Jane Smith<br/>Joe linebreaks<br />Alice Third",
     (WARN, [Complaint.CONTAINS_HTML])),
    (
        "C. Sivaram (1) and Kenath Arun (2) ((1) Indian Institute of Astrophysics, Bangalore, (2) Christ Junior College, Bangalore)",
        None,
    ),  # should not flag physics in astrophys as inappropriate
    ("Sylvie Roux", None),
    ("S Roux", None),
    ("Jaganathan SR", None),
    ("Sylvie ROUX", None),  # ?
    ("S ROUX", None),
    # ("SYLVIE ROUX", (WARN, [Complaint.EXCESSIVE_CAPITALIZATION])),
    ("SYLVIE ROUX", None),
    ("Sylvie roux", None),  # ?
    # TODO:
    # ("sylvie roux", (WARN, [Complaint.NO_CAPS_IN_NAME])),
    ("Sylvie Roux [MIT]",
     (WARN, [Complaint.BAD_CHARACTER])),
    ("Jennifer 8 Lee",  # An actual name
     (WARN, [Complaint.CONTAINS_NUMBER]),
    ),
    # The 2023 Windows on the Universe Workshop White Paper Working Group: T. Ahumada, J. E. Andrews, S. Antier, E. Blaufuss,
    ("Someone Smith Physics Dept",
     (WARN, [Complaint.CONTAINS_AFFILIATION])),
    # 'Authors: name should not contain Physics',
    # 'Authors: name should not contain Dept'])),
    # TODO: ("Smith", (WARN, [Complaint.CONTAINS_LONE_SURNAME])),
    # (
    #     "Fred Smith, Bloggs",
    #     # (WARN, [Complaint.'Authors: only surname? Bloggs'])),
    #     (WARN, [Complaint.CONTAINS_LONE_SURNAME]),
    # ),
    ("Author: Fred Smith",
     (WARN, [Complaint.BEGINS_WITH_AUTHOR])),
    ("Authors: J. Smith, Joe Bob, and Mr. Briggs",
     (WARN, [Complaint.BEGINS_WITH_AUTHOR])),
    ("Fred Smith (1), ((1) Cornell)", None),
    # ('Fred Smith(1), ((1) Cornell)','Authors: missing spaces around parenthesis'),
    # ('Fred Smith (1), ((1)Cornell)','Authors: missing spaces around parenthesis'),
    ("Fred Smith, Joan Alter", None),
    ("Fred Smith, , Joan Alter",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    # JHY: this is tricky!
    ("Fred Smith,Joan Alter", None),
    #  (WARN, [Complaint.EXTRA_WHITESPACE])),
    ("Fred Smith ,Joan Alter",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    ("Fred Smith (Cornell)", None),
    ("Fred Smith (Cornell), Bob Smith (MIT)", None),
    ("Hsi-Sheng Goan*, Chung-Chin Jian, Po-Wen Chen",
     (WARN, [Complaint.BAD_CHARACTER])),
    (
        "Ph\\`ung H\\^o Hai, Jo\\~ao Pedro dos Santos, Pham Thanh T\\^am, {\\DJ}\\`ao V\\u{a}n Thinh",
        None,
    ),
    ("Fred Smith~Jones",
     (WARN, [Complaint.TILDE_AS_HARD_SPACE])),
    # ('Zhe-Xuan Gong G.-D. Lin L.-M.','Authors: surprisingly low number of commas|Authors: ends with punctuation (.)'),
    # ('Zhe-Xuan Gong G.-D. Lin L.-M. Duan','Authors: surprisingly low number of commas'),
    # TODO: We don't check for this yet
    # ('S. B?oser',
    #  (WARN, [Complaint.'Authors: unexpected question mark, perhaps bad 8-bit conversion?'])),
    ('M. Bonarota, J.-L. Le Gou\\"et, T. Chaneli\\`ere', None),
    # ('M. Bonarota, et. al',"Authors: 'et al' incorrectly punctuated"),
    (
        "P. J. Crockett, M. Mathioudakis, D. B. Jess, S. Shelyag, F. P. Keenan, D. J. Christian",
        None,
    ),
    (
        "Thomas Brettschneider and Giovanni Volpe and Laurent Helden and Jan Wehr and Clemens Bechinger",
        None,
    ),
    ("R. T. Wicks, T. S. Horbury, C. H. K. Chen, and A. A. Schekochihin", None),
    ("Guillermo A. Lemarchand,",
     (WARN, [Complaint.TRAILING_PUNCTUATION])),
    # ('Ralf Sch\\"utzhold, William G.~Unruh',"Authors: tilde as hard space?"),
    ("Jean Nu\\~nos", None),
    # NOTE: The tests below require parsing the author string
    # NOTE: the author parser really messes up here.
    # ("Fred Smith B.S., Joe Bloggs",
    #  (WARN, [Complaint.CONTAINS_INITIALS]),
    # ),
    # ["Authors: initials after surname?"])),
    # (
    #     "Fred S., Joe Bloggs",
    #     (WARN, [Complaint.CONTAINS_INITIALS]),
    # ),  # ["Authors: initial in surname?"])),
    ("Fred S, Joe B", None),  # per discussion 12 May 2025
    # ('Fred S, Joe Bloggs',
    #  (WARN, [Complaint.CONTAINS_INITIALS])), # ["Authors: initial in surname?"])),
    # ('Fred Smith, Joe Bloggs et al',"Authors: et al punctuation"),
    # ('Fred Smith \'and\' Joe Bloggs',"Authors: has literal quoted 'and' in it (change to plain and?)"),
    ("Fred Smith, (Joe Bloggs",
     (WARN, [Complaint.UNBALANCED_BRACKETS])),
    # ('Fred Smith, 1040 West Addison',"Authors: postal address?"),
    ## ('UNIV of Hard Knocks',"Authors: uppercase surname or incorrectly formatted institution"),
    ("Fred Smith, Joe Bloggs, Univ of Hard Knocks",
     (WARN, [Complaint.CONTAINS_AFFILIATION])),
    ("Arthur Rubinstein, Devika Kamath, A. Taraphder, and Stefano Profumo", None),
    ("Bloss, Adrienne and Cornish, Audie",
     (WARN, [Complaint.CONTAINS_LONE_SURNAME])),
    ('Paul R.~Archer',
     (WARN, [Complaint.TILDE_AS_HARD_SPACE])),
    # "Authors: includes semicolon not in affiliation, comma intended?"
    ("Ancille Ngendakumana; Joachim Nzotungicimpaye",
     (WARN, [Complaint.CONTAINS_SEMICOLON])),
    # (
    #     "Ngendakumana, Ancille; Nzotungicimpaye, Joachim",
    #     (
    #         WARN,
    #         [
    #             CONTAINS_LONE_SURNAME,  # "Authors: lone surname",
    #             BAD_CHARACTER,  # "Authors: name should not contain ;",
    #         ],
    #     ),
    # ),
    # Failing (WHY?)
    # ("Stefano Liberati (SISSA, INFN; Trieste), Carmen Molina-Paris (Los Alamos)", None),
    ("Stefano Liberati (SISSA, INFN; Trieste) and Carmen Molina-Paris (Los Alamos)", None),
    # No spaces before close or after open parens
    ("Stefano Liberati ( SISSA, INFN; Trieste)",
     (WARN, [Complaint.UNNECESSARY_SPACE_IN_PARENS])),
    ("Stefano Liberati (SISSA, INFN; Trieste )",
     (WARN, [Complaint.UNNECESSARY_SPACE_IN_PARENS])),
    ("Stefano Liberati; Carmen Molina-Paris",
     (WARN, [Complaint.CONTAINS_SEMICOLON])),
    # ('A.N.~Author, O K Author','Authors: tilde as hard space?'),
    ('T. L\\"u', None),
    ('T. Cs\\"org\\H{o}', None),
    ('Barney Smity.',
     (WARN, [Complaint.TRAILING_PUNCTUATION])),
    ('Barney Smity III.',
     (WARN, [Complaint.TRAILING_PUNCTUATION])),
    ("T. Y{\\i}ld{\\i}z", None),
    ("T. Zaj\\k{a}c", None),
    ("(T. Zaj\\k{a}c",
     (WARN, [Complaint.UNBALANCED_BRACKETS])),
    # LLM examples...
    ("Joe Llama", None),  # really...
    ("Llamallama",
     (WARN, [Complaint.CONTAINS_LONE_SURNAME])),
    ("Llama",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED])),
    ("Adrienne Bloss, Audie Cornish, and ChatGPT",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED])),
    ("Jonathan Young and ChatGPT",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED])),
    # CAREFUL: this parses into a first name "GPT-3." and a surname, "5" !?
    ("GPT-3.5",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED, Complaint.CONTAINS_NUMBER])),
    ("GPT-4",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED, Complaint.CONTAINS_NUMBER])),
    ("GPT-4.5",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED, Complaint.CONTAINS_NUMBER])),
    ("GPT-5",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED, Complaint.CONTAINS_NUMBER])),
    ("Claude Sonnet 4",
     (WARN, [Complaint.CONTAINS_NUMBER])),
    ("Gemini 2.5 Pro",
     (WARN, [Complaint.LLM_AUTHOR_DETECTED, Complaint.CONTAINS_NUMBER])),
]


@pytest.mark.parametrize("test", AUTHORS_TESTS)
def test_authors(test):
    (authors, expected_result) = test
    metadata = Metadata()
    metadata.authors = authors
    result = metacheck.check(metadata)
    print( authors, result )
    check_result(result[AUTHORS], expected_result)


############################################################
##### Detailed tests for ABSTRACT field

ABSTRACT_TESTS = [
    ("In this work, we study aaa, bbb, and ccc and conclude ddd.", None),
    ("About YBa$_{2}$Cu$_{3}$O$_{6.95}$", None),
    ("Both \\phi and \\varphi may be used", None),
    ("Abstract: some text",
     (WARN, [Complaint.BEGINS_WITH_ABSTRACT])),
    # Excess whitespace, 3 cases
    (" This contains a leading space",
     (WARN, [Complaint.LEADING_WHITESPACE])),
    ("This contains a trailing space ",
     (WARN, [Complaint.TRAILING_WHITESPACE])),
    ("This contains  two spaces",
     (WARN, [Complaint.EXTRA_WHITESPACE])),
    ("Abstractive summarization is ok", None),
    # ['  abstract : here  ',"Abstract: starts with the word Abstract, remove"],
    ("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>", None),
    # ['Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>','Abstract: HTML elements: <sup> </sup> <sup> </sup>'],
    # ['With HTML<br/>linebreaks<br />there','Abstract: HTML elements: <br/> <br />'],
    # 30 Apr 2025: line breaks in abstracts really aren't that bad.
    (
        "Some words\\\\\\\\ more words",
        # (WARN, [Complaint.BAD_CHARACTER])),
        None,
    ),
    # (MathJax now handles "$3$-coloring")
    ("Work \\cite{8} established a connection between the edge $3$-coloring", None),
    # Don't allow empty paragraphs or spaces at the end of paragraphs!
    ("Work established\n \n\n a connection between the edge $3$-coloring",
     (WARN, [Complaint.EXTRA_WHITESPACE_ABS])),
    ("Work established  \na connection between the edge $3$-coloring",
     (WARN, [Complaint.EXTRA_WHITESPACE_ABS])),
    # Paragraphs can be indented, though!
    ("Work established\n a connection between the edge $3$-coloring",
     None),
    ("Work established a connection between the edge $3$-coloring ",
     (WARN, [Complaint.TRAILING_WHITESPACE])),
    # Not yet:
    # ('he abstract is sometimes missing a first letter, warn if starts with lower',
    # (WARN, [Complaint.'Abstract: starts with lower case']
    # ["Lone periods should not be allowed.\\n.\\n",'Abstract: lone period, remove or it will break the mailing!'],
    ("This \\ is not a line break", None),
    ("Control characters \u0003 are not permitted",
     (WARN, [Complaint.CONTAINS_CONTROL_CHARS_ABS])),
    ("Control characters (including tabs)\tare not permitted",
     (WARN, [Complaint.CONTAINS_CONTROL_CHARS_ABS])),
    ("Newlines\nare permitted", None),
    ("Paragraphs\n \nwith only whitespace are not permitted",
     (WARN, [Complaint.EXTRA_WHITESPACE_ABS])),
    # TeX line breaks are also permitted
    ("This \\\\ is a line break", None),
    # check for \n not followed by 2 spaces (paragraph marker)
    # (
    #     "This contains \na line break (no spaces)",
    #     (
    #         WARN,
    #         [
    #             BAD_CHARACTER  # "Abstract: contains \\n (line break)"
    #         ],
    #     ),
    # ),
    # (
    #     "This contains \n a line break (one space)",
    #     (
    #         WARN,
    #         [
    #             BAD_CHARACTER  # "Abstract: contains \\n (line break)"
    #         ],
    #     ),
    # ),
    # JHY This is problematic
    # ('This contains \n  a paragraph break (see the spaces)', None),
    # (
    #     "Don't use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something",
    #     (
    #         WARN,
    #         [
    #             Complaint.BAD_CHARACTER,
    #         ],
    #     ),
    # ),
    ("This ] is bad",
     (WARN, [Complaint.UNBALANCED_BRACKETS])),
    (
        "Учењето со засилување е разноврсна рамка за учење за решавање на сложени задачи од реалниот свет. Конечно, разговараме за отворените предизвици на техниките за анализа за RL алгоритми.",
        (WARN, [Complaint.MUST_BE_ENGLISH]),
    ),
    (
        "El aprendizaje por refuerzo es un marco versátil para aprender a resolver tareas complejas del mundo real. Sin embargo, las influencias en el rendimiento de aprendizaje de los algoritmos de aprendizaje por refuerzo suelen comprenderse mal en la práctica.",
        (WARN, [Complaint.MUST_BE_ENGLISH]),
    ),
    # POST-MVP, this should warn if contains TeX: (WARN, [Complaint.CONTAINS_TEX])),
    ("\\begin{abstract}This uses some TeX\\end{abstract}", None)
]


@pytest.mark.parametrize("test", ABSTRACT_TESTS)
def test_abstracts(test):
    (abstract, expected_result) = test
    metadata = Metadata()
    metadata.abstract = abstract
    result = metacheck.check(metadata)
    print(abstract, result, expected_result)
    check_result(result[ABSTRACT], expected_result)


############################################################
##### Detailed tests for COMMENTS field

COMMENTS_TESTS = [
    ("", None),
    ("A comment", None),
    ("15 pages, 6 figures", None),
    ("A comment with èéêëìíîï accents", None),
    (
        "A comment with èéêëìíîï accents".encode("UTF-8").decode("LATIN-1"),
        (WARN, [Complaint.BAD_UNICODE_ENCODING]),
    ),
    ("A comment with 普通话 Chinese", None),
    (
        "A comment with 普通话 Chinese".encode("UTF-8").decode("LATIN-1"),
        (WARN, [Complaint.BAD_UNICODE_ENCODING]),
    ),
    # ('15 pages, 6 figures,',(HOLD,['Comments: ends with punctuation (,)'])],
    # ['15 pages, 6 figures:',(HOLD,['Comments: ends with punctuation (:)'])],
    # ['Comments: 15 pages, 6 figures',(HOLD,['Comments: starts with the word Comments, check'])],
    # ['Poster submission to AHDF',(HOLD,["Comments: contains word 'poster'"])],
    # (
    #     "Don't use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something",
    #     (
    #         WARN,
    #         [
    #             Complaint.CONTAINS_TEX,
    #         ],
    #     ),
    # ),
    ("This ] is bad", (WARN, [Complaint.UNBALANCED_BRACKETS])),
]


@pytest.mark.parametrize("test", COMMENTS_TESTS)
def test_comments(test):
    (comments, expected_result) = test
    metadata = Metadata()
    metadata.comments = comments
    result = metacheck.check(metadata)
    # print( comments, result )
    check_result(result[COMMENTS], expected_result)


############################################################
##### Detailed tests for REPORT-NO field

REPORT_NO_TESTS = [
    ["LANL-UR/2001-01", None],
    ["ITP 09 #1", None],
    ["NO-NUM",
     (HOLD, [Complaint.MUST_CONTAIN_DIGITS])],
    ["12",
     (WARN, [Complaint.TOO_SHORT])],
    ["123",
     (WARN, [Complaint.TOO_SHORT])],
    ["1234",
     (HOLD, [Complaint.MUST_CONTAIN_LETTERS])],
    ["12345",
     (HOLD, [Complaint.MUST_CONTAIN_LETTERS])],
]


@pytest.mark.parametrize("test", REPORT_NO_TESTS)
def test_report_num(test):
    (report_num, expected_result) = test
    metadata = Metadata()
    metadata.report_num = report_num
    result = metacheck.check(metadata)
    # print( report_num, result )
    check_result(result[REPORT_NUM], expected_result)


############################################################
##### journal_ref field checks

JREF_TESTS = [
    # ['ibid',"Journal-ref: inappropriate word: ibid"],
    ("jref",
     (WARN, [Complaint.TOO_SHORT])),
    ("1975",
     (WARN, [Complaint.TOO_SHORT])),
    ("Proceedings of the 34th \"The Web Conference\" (WWW 2025)", None),
    ("JACM volume 1 issue 3, Jan 2024", None),
    # Removed Oct 2025?
    # ("Science 1.1",
    #  (WARN, [Complaint.MUST_CONTAIN_YEAR])),
    ("Science 1.1", None),
    ("JACM Jan 2024 DOI:10.2345/thisisnotadoi",
     (WARN, [Complaint.CONTAINS_DOI])),
    ("Accepted for publication in JACM Jan 2024",
     (WARN, [Complaint.CONTAINS_ACCEPTED])),
    ("Submitted to JACM Jan 2024",
     (WARN, [Complaint.CONTAINS_SUBMITTED])),
    # ['Science SPIE 1.1',"Journal-ref: submission from SPIE conference? Check for copyright issues"],
]


@pytest.mark.parametrize("test", JREF_TESTS)
def test_jrefs(test):
    journal_ref, expected_result = test
    metadata = Metadata()
    metadata.journal_ref = journal_ref
    result = metacheck.check(metadata)
    # print( journal_ref, result )
    check_result(result[JOURNAL_REF], expected_result)


############################################################
# (related DOI?) DOI field checks

DOI_TESTS = [
    ["10.485",
     (WARN, [Complaint.TOO_SHORT])],
    ["10",
     (WARN, [Complaint.TOO_SHORT])],
    ["10.48550/arXiv.2501.18183", None],
    ["22.48550/arXiv.2501.18183", None], # YES, this is valid!
    ["doi.org/10.48550/arXiv.2501.18183",
     (WARN, [Complaint.INVALID_DOI, Complaint.CONTAINS_DOI2])],
    ["doi:10.48550/arXiv.2501.18183",
     (WARN, [Complaint.INVALID_DOI, Complaint.CONTAINS_DOI2])],
    ["doi:22.48550/arXiv.2501.18183",
     (WARN, [Complaint.INVALID_DOI, Complaint.CONTAINS_DOI2])],
    ["1234556789",
     (WARN, [Complaint.INVALID_DOI])],     
    ["1234556789/arXiv.2501.18183",
     (WARN, [Complaint.INVALID_DOI])],     
    ["https://doi.org/10.48550/arXiv.2501.18183",
     (WARN, [Complaint.INVALID_DOI, Complaint.CONTAINS_URL, Complaint.CONTAINS_DOI2])],
    # ["http://doi.org/10.48550/arXiv.2501.18183",
    #  (WARN, [Complaint.CONTAINS_URL])],
    # TODO: Should this be valid, or not?
    ['I like 10.48550/arXiv.2501.18183',
     (WARN, [Complaint.INVALID_DOI])],
]


@pytest.mark.parametrize("test", DOI_TESTS)
def test_doi(test):
    (doi, expected_result) = test
    metadata = Metadata()
    metadata.doi = doi
    result = metacheck.check(metadata)
    print( doi, result )
    check_result(result[DOI], expected_result)


############################################################
#

MSC_CLASS_TESTS = [
    ["", None],
    ["abc", None],    
    ["abc def", None],
    ["  abc",
     (WARN, [Complaint.LEADING_WHITESPACE])],
    ["abc  def",
     (WARN, [Complaint.EXTRA_WHITESPACE])],
    ["abcdef  ",
     (WARN, [Complaint.TRAILING_WHITESPACE])],
    ["abc\ndef",
     (WARN, [Complaint.CONTAINS_CONTROL_CHARS])],
]


@pytest.mark.parametrize("test", MSC_CLASS_TESTS)
def test_msc_class(test):
    (msc_class, expected_result) = test
    metadata = Metadata()
    metadata.msc_class = msc_class
    result = metacheck.check(metadata)
    # print( msc_class, result )
    check_result(result[MSC_CLASS], expected_result)

############################################################
# ACM CLASS ? 


############################################################
#

BALANCED_BRACKETS_TESTS = [
    "10.48550/arXiv.2501.18183((()))",
    "(([[{{}}]]))",
    "(({}[[]])())[]",
]

UNBALANCED_BRACKETS_TESTS = [
    "this [ is wrong",
    "this [ } wrong",
    "this [ ) wrong",
    "this ( is wrong",
    "this ( ] wrong",
    "this ( } wrong",
    "this { is wrong",
    "this { ) wrong",
    "this { ] wrong",
    "this is ) ( wrong",
    "this is } wrong",
    "this is ] [ wrong",
]


@pytest.mark.parametrize("s", BALANCED_BRACKETS_TESTS)
def test_balanced_brackets(s):
    assert metacheck.all_brackets_balanced(s) == True


@pytest.mark.parametrize("s", BALANCED_BRACKETS_TESTS)
def test_unbalanced_brackets(s):
    assert metacheck.all_brackets_balanced(s) == True


############################################################
#


def test_long_word_caps():
    assert not long_word_caps("HOMESTAKE")
    assert not long_word_caps("THISISALONGWORD")
    assert not long_word_caps("THISISALONGWORD not long NOT LONG")
    # HOMESTAKE is a known allcaps word
    assert not long_word_caps("THISISALONGWORD HOMESTAKE")
    assert not long_word_caps("THISISALONGWORD 123456789")
    assert long_word_caps("THISISALONGWORD not long VERYLONGWORD")


# pyenv activate arxiv-base-3-11
# sudo apt install -y protobuf-compiler
# poetry install --with=dev --extras qa
# python -m pytest arxiv/metadata/tests/test_metacheck.py

# print( "Stefano Liberati (SISSA, INFN; Trieste), Carmen Molina-Paris (Los Alamos)"[19:21] )

def test_offsets():
    title = "this  is \\\\ a BADBADBAD TITLELONG LONGTITLE"
    metadata = Metadata()
    metadata.title = title
    result = metacheck.check(metadata)
    # print(test, result, expected_result)
    print( result )
    print("Complaints:")
    for k in result[TITLE].get_complaints():
        print( k )
        print( "Offsets: ", result[TITLE].get_offsets()[k] )
        for (s,e) in result[TITLE].get_offsets()[k]:
            print( k, s, e, ">", title[s:e], "<" )
            BAD_STRINGS = (
                "t",            # Begins 
                "s  i",
                "\\\\",
                "BADBADBAD", "TITLELONG", "LONGTITLE")
            assert title[s:e] in BAD_STRINGS

    #

test_offsets()
