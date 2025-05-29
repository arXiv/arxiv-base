
import pytest

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


try:
    from arxiv.metadata.metacheck import combine_dispositions
except ModuleNotFoundError:
    pytest.skip(
        """"gcld3 and/or protobuf-compile are not installed.
            To run these tests, install with:
            sudo apt install -y protobuf-compiler
            poetry install --with-dev --extras qa""", allow_module_level=True)

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

OK = Disposition.OK
WARN = Disposition.WARN
HOLD = Disposition.HOLD

CANNOT_BE_EMPTY = Complaint.CANNOT_BE_EMPTY
TOO_SHORT = Complaint.TOO_SHORT
CONTAINS_BAD_STRING = Complaint.CONTAINS_BAD_STRING
EXCESSIVE_CAPITALIZATION = Complaint.EXCESSIVE_CAPITALIZATION
UNBALANCED_BRACKETS = Complaint.UNBALANCED_BRACKETS
BAD_UNICODE = Complaint.BAD_UNICODE
CONTAINS_LONE_SURNAME = Complaint.CONTAINS_LONE_SURNAME
CONTAINS_INITIALS = Complaint.CONTAINS_INITIALS
NO_CAPS_IN_NAME = Complaint.NO_CAPS_IN_NAME
MUST_CONTAIN_LETTERS = Complaint.MUST_CONTAIN_LETTERS
MUST_CONTAIN_DIGITS = Complaint.MUST_CONTAIN_DIGITS
MUST_CONTAIN_YEAR = Complaint.MUST_CONTAIN_YEAR
MUST_BE_ENGLISH = Complaint.MUST_BE_ENGLISH

############################################################
# Helper functions for unit tests

def check_result( result: MetadataCheckReport,
                  expected: Optional[Tuple[Disposition, List[Complaint]]] ):
    # result should be ( OK, [] ) or (HOLD, [message, message...]) or (WARN, ...)
    if expected is None:
        assert result.get_disposition() == OK
    else:
        assert result.disposition == expected[0]
        assert list(result.get_complaints()) != None
        # TODO: test complaints with context, too?
        assert list(result.get_complaints()) == expected[1]
    #


############################################################
# Tests for internal (helper) function combine_dispositions

def test_combine_dispositions():
    assert HOLD == combine_dispositions( HOLD, HOLD )
    assert HOLD == combine_dispositions( HOLD, WARN )
    assert HOLD == combine_dispositions( WARN, HOLD )
    assert HOLD == combine_dispositions( HOLD, OK )
    assert HOLD == combine_dispositions( OK, HOLD )
    assert WARN == combine_dispositions( WARN, WARN )
    assert WARN == combine_dispositions( WARN, OK )
    assert WARN == combine_dispositions( OK, WARN )
    assert OK == combine_dispositions( OK, OK )

############################################################l
##### TITLE field checks

TITLE_TESTS = [
    ('A fine title', None),
    ('Another title about CERN and ALPEH where z~1/2', None),
    ('',
     (HOLD, [CANNOT_BE_EMPTY])),
    ('Tiny',
     (WARN, [TOO_SHORT])),
    ('a title with lowercase',
     (WARN, [CONTAINS_BAD_STRING])),
    # Fewer than 0.25% of all papers start with a lower-case letter,
    # but there are some patterns, which we are not checking for:
    ('aTITLE: Not So Lowercase',
     (WARN, [CONTAINS_BAD_STRING])),
    # NOTE: we don't check for extra spaces
    # ['  A title with leading space',"Title: leading spaces"],
    # ['A title with trailing space ',"Title: trailing spaces"],
    # ['A title  with  mutliple  spaces',"Title: multiple consecutive spaces"],
    # NOTE: Titles can end with punctuation.
    ('A title with period.', None),
    # NOTE: the test for excessive capitalization is fragile
    ('ALL CAPS TITLE',
     (WARN, [CONTAINS_BAD_STRING])),
    ('NOT EVEN BORDERLINE ALL CAPS TITLE',
     (WARN, [CONTAINS_BAD_STRING])),
    ('BORDERLINE All Caps TITLE', None),
    ('BORDERLINE ALL caps TITLE', 
     (WARN, [CONTAINS_BAD_STRING])),
    ('This is a title WITH ONE LONG WORD CAPITALIZED', None),
    ('This is a title WITH SOME EXTRAEXTRA LONG WORDS CAPITALIZED',
     [WARN, [CONTAINS_BAD_STRING]]),
    # We allow some capitalized words
    ('The is a title with known long words capitalized AMANDA CHANDRA', None),
    # But in general, we complain if there are 2 or more capitalized words
    ('The is a title with unknown long words capitalized UNIQUEWORD THISISATEST',
     [WARN, [CONTAINS_BAD_STRING]]),
    # but digit strings don't count
    ('The is a title with 12345678 and 987654321 words not capitalized', None),
    # Check for *some* HTML entities
    ('These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>', None),
    ('Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>',
     (WARN, [CONTAINS_BAD_STRING])),
    ('A title with HTML<br/>linebreaks<br />there',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Title: Something',
     (WARN, [CONTAINS_BAD_STRING])),
    ('This \\ is not a line break', None),
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Line break at end\\\\',
     (WARN, [CONTAINS_BAD_STRING])),
    ('This \\ is not a line break', None),
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [CONTAINS_BAD_STRING
         # 'Title: contains \\href',
         # 'Title: contains \\url',
         # 'Title: contains \\emph',
         # 'Title: contains \\uline',
         # 'Title: contains \\textbf',
         # 'Title: contains \\texttt',
         # 'Title: contains unnecessary escape: \\#',
         # 'Title: contains unnecessary escape: \\%',
     ])),
]

@pytest.mark.parametrize("test", TITLE_TESTS)
def test_titles(test):
    title, expected_result = test
    result = metacheck.check( { TITLE: title } );
    # print(test, result, expected_result)
    check_result(result[TITLE], expected_result)

############################################################
##### Detailed tests for AUTHORS field

AUTHORS_TESTS = [
    # ('',
    #  (HOLD, [CANNOT_BE_EMPTY])),
    ('C Li', None),
    ('Li C', None),
    ("C C", 
     (WARN, [TOO_SHORT])),
    ('Fred Smith', None),
    ('Fred Smith, Joe Bloggs', None),
    # We don't check for ellipsis, but
    # ('Fred Smith, Joe Bloggs, ...',
    #  (WARN, ["Authors: ends with punctuation"])),
    ('Fred Smith, \\ Joe Bloggs', None ),
    ('Fred Smith, \\\\ Joe Bloggs',     
     (WARN, [CONTAINS_BAD_STRING])),
    ('Fred Smith*, Joe Bloggs#, Bob Briggs^, Jill Camana@, and Rebecca MacInnon',     
     (WARN, [CONTAINS_BAD_STRING])),
    # "Authors: contains bad character '*'",
    # "Authors: contains bad character '#'",
    # "Authors: contains bad character '^'",
    # "Authors: contains bad character '@'",         
    (' Jane  Austen ',
     (WARN, [CONTAINS_BAD_STRING])),
    # "Authors: leading whitespace",
    # "Authors: trailing whitespace",
    # "Authors: excess whitespace",
    ('Jane Jones (Austen Nname',
     (WARN, [UNBALANCED_BRACKETS])),
    # ('Fred Smith(University), Joe Bloggs',"Authors: missing spaces around parenthesis"),
    ('Martha Raddatz , Ayesha Rascoe',
     (WARN, [CONTAINS_BAD_STRING])),
    # ('Fred Smith & Joe Bloggs',"Authors: possibly inappropriate ampersand"),
    ('Person with <sup>1</sup>',
     (WARN, [CONTAINS_BAD_STRING,
             # 'Authors: no caps in name',
             # 'Authors: name should not contain digits',             
             ])), 
    ('Jane Smith<br/>Joe linebreaks<br />Alice Third',
     (WARN, [CONTAINS_BAD_STRING])),
    ('C. Sivaram (1) and Kenath Arun (2) ((1) Indian Institute of Astrophysics, Bangalore, (2) Christ Junior College, Bangalore)', None), # should not flag physics in astrophys as inappropriate
    ('Sylvie Roux', None),
    ('S Roux', None),
    ('Jaganathan SR', None),
    ('Sylvie ROUX', None),      # ?
    ('S ROUX', None),
    ('SYLVIE ROUX', 
     (WARN, [EXCESSIVE_CAPITALIZATION])),
    ('Sylvie roux', None),      # ?
    ('sylvie roux',
     (WARN, [NO_CAPS_IN_NAME])),
    ('Sylvie Roux [MIT]',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Jennifer 8 Lee',          # An actual name
     (WARN, [CONTAINS_BAD_STRING])),
    # The 2023 Windows on the Universe Workshop White Paper Working Group: T. Ahumada, J. E. Andrews, S. Antier, E. Blaufuss, 
    ('Someone Smith Physics Dept',
     (WARN, [CONTAINS_BAD_STRING])),
         # 'Authors: name should not contain Physics',
         # 'Authors: name should not contain Dept'])),
    ('Smith',
     (WARN, [CONTAINS_LONE_SURNAME])),
    ('Fred Smith, Bloggs',
     # (WARN, ['Authors: only surname? Bloggs'])),
     (WARN, [CONTAINS_LONE_SURNAME])),
    ('Author: Fred Smith',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Authors: J. Smith, Joe Bob, and Mr. Briggs',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Fred Smith (1), ((1) Cornell)', None),
    # ('Fred Smith(1), ((1) Cornell)','Authors: missing spaces around parenthesis'),
    # ('Fred Smith (1), ((1)Cornell)','Authors: missing spaces around parenthesis'),
    ('Fred Smith (Cornell)', None),
    ('Fred Smith (Cornell), Bob Smith (MIT)', None),
    ('Hsi-Sheng Goan*, Chung-Chin Jian, Po-Wen Chen',
     (WARN, [CONTAINS_BAD_STRING])),
    ("Ph\\`ung H\\^o Hai, Jo\\~ao Pedro dos Santos, Pham Thanh T\\^am, {\\DJ}\\`ao V\\u{a}n Thinh",
     None),
    # ('Zhe-Xuan Gong G.-D. Lin L.-M.','Authors: surprisingly low number of commas|Authors: ends with punctuation (.)'),
    # ('Zhe-Xuan Gong G.-D. Lin L.-M. Duan','Authors: surprisingly low number of commas'),
    # TODO: We don't check for this yet
    # ('S. B?oser',
    #  (WARN, ['Authors: unexpected question mark, perhaps bad 8-bit conversion?'])),
    ('M. Bonarota, J.-L. Le Gou\\"et, T. Chaneli\\`ere', None),
    # ('M. Bonarota, et. al',"Authors: 'et al' incorrectly punctuated"),
    ('P. J. Crockett, M. Mathioudakis, D. B. Jess, S. Shelyag, F. P. Keenan, D. J. Christian', None),
    ('Thomas Brettschneider and Giovanni Volpe and Laurent Helden and Jan Wehr and Clemens Bechinger', None),
    ('R. T. Wicks, T. S. Horbury, C. H. K. Chen, and A. A. Schekochihin', None),
    ('Guillermo A. Lemarchand,',
     (WARN, [CONTAINS_BAD_STRING])),
    # ('Ralf Sch\\"utzhold, William G.~Unruh',"Authors: tilde as hard space?"),
    ('Jean Nu\\~nos', None),
    # NOTE: The tests below require parsing the author string
    # NOTE: the author parser really messes up here.
    ('Fred Smith B.S., Joe Bloggs',
     (WARN, [CONTAINS_INITIALS])), # ["Authors: initials after surname?"])),
    ('Fred S., Joe Bloggs',
     (WARN, [CONTAINS_INITIALS])), # ["Authors: initial in surname?"])),
    ('Fred S, Joe B', None),       # per discussion 12 May 2025
    # ('Fred S, Joe Bloggs',
    #  (WARN, [CONTAINS_INITIALS])), # ["Authors: initial in surname?"])),
    # ('Fred Smith, Joe Bloggs et al',"Authors: et al punctuation"),
    # ('Fred Smith \'and\' Joe Bloggs',"Authors: has literal quoted 'and' in it (change to plain and?)"),
    ('Fred Smith, (Joe Bloggs',
     (WARN, [UNBALANCED_BRACKETS])),
    # ('Fred Smith, 1040 West Addison',"Authors: postal address?"),
    ## ('UNIV of Hard Knocks',"Authors: uppercase surname or incorrectly formatted institution"),
    ('Fred Smith, Joe Bloggs, Univ of Hard Knocks',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Arthur Rubinstein, Devika Kamath, A. Taraphder, and Stefano Profumo',
     None),
    ('Joe Llama', None),        # really...
    ('Llama',
     (WARN, [
         CONTAINS_LONE_SURNAME, # "Authors: lone surname",
         CONTAINS_BAD_STRING, # "Authors: name should not contain Llama",
     ])),
    ('Adrienne Bloss, Audie Cornish, and ChatGPT',
     (WARN, [
         CONTAINS_LONE_SURNAME, # "Authors: lone surname",
         CONTAINS_BAD_STRING, # "Authors: name should not contain ChatGPT",
     ])),
    ('Bloss, Adrienne and Cornish, Audie',
     (WARN, [
         CONTAINS_LONE_SURNAME, # "Authors: lone surname",
     ])),
    # ('Paul R.~Archer', "Authors: tilde as hard space?"),
    # "Authors: includes semicolon not in affiliation, comma intended?"
    ('Ancille Ngendakumana; Joachim Nzotungicimpaye',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Ngendakumana, Ancille; Nzotungicimpaye, Joachim',
     (WARN, [
         CONTAINS_LONE_SURNAME, # "Authors: lone surname",
         CONTAINS_BAD_STRING, # "Authors: name should not contain ;",
     ])),
    ('Stefano Liberati (SISSA, INFN; Trieste), Carmen Molina-Paris (Los Alamos)', None),
    # ('A.N.~Author, O K Author','Authors: tilde as hard space?'),
    ('T. L\\"u', None),
    ('T. Cs\\"org\\H{o}', None),
    ('T. Y{\\i}ld{\\i}z', None),
    ('T. Zaj\\k{a}c', None),
    ('(T. Zaj\\k{a}c',
     (WARN, [UNBALANCED_BRACKETS])),
]

@pytest.mark.parametrize("test", AUTHORS_TESTS)
def test_authors(test):
    (authors, expected_result) = test
    result = metacheck.check( { AUTHORS: authors } )
    # print( authors, result )
    check_result(result[AUTHORS], expected_result)

############################################################
##### Detailed tests for ABSTRACT field

ABSTRACT_TESTS = [
    ('In this work, we study aaa, bbb, and ccc and conclude ddd.', None),
    ('About YBa$_{2}$Cu$_{3}$O$_{6.95}$', None),
    ('Both \\phi and \\varphi may be used', None),
    ('Abstract: some text',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Abstractive summarization is ok', None),
    # ['  abstract : here  ',"Abstract: starts with the word Abstract, remove"],
    ('These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>', None),
    # ['Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>','Abstract: HTML elements: <sup> </sup> <sup> </sup>'],
    # ['With HTML<br/>linebreaks<br />there','Abstract: HTML elements: <br/> <br />'],
    # 30 Apr 2025: line breaks in abstracts really aren't that bad.
    ('Some words\\\\\\\\ more words',
     # (WARN, [CONTAINS_BAD_STRING])),
     None),
    # (MathJax now handles "$3$-coloring")
    ('Work \\cite{8} established a connection between the edge $3$-coloring', None),
    # Not yet:
    # ('he abstract is sometimes missing a first letter, warn if starts with lower',
    # (WARN, ['Abstract: starts with lower case']
    # ["Lone periods should not be allowed.\\n.\\n",'Abstract: lone period, remove or it will break the mailing!'],
    ('This \\ is not a line break', None),
    # This is now permitted
    ('This \\\\ is a line break', None),
    # check for \n not followed by 2 spaces (paragraph marker)
    ('This contains \na line break (no spaces)',
     (WARN, [CONTAINS_BAD_STRING # "Abstract: contains \\n (line break)"
             ])),
    ('This contains \n a line break (one space)',
     (WARN, [CONTAINS_BAD_STRING # "Abstract: contains \\n (line break)"
             ])),
    ('This contains \n  a paragraph break (see the spaces)', None),
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [
         CONTAINS_BAD_STRING,
     ])),            
    ('This ] is bad',
     (WARN, [UNBALANCED_BRACKETS])),
    ('Учењето со засилување е разноврсна рамка за учење за решавање на сложени задачи од реалниот свет. Конечно, разговараме за отворените предизвици на техниките за анализа за RL алгоритми.',
     (WARN, [MUST_BE_ENGLISH])),
    ('El aprendizaje por refuerzo es un marco versátil para aprender a resolver tareas complejas del mundo real. Sin embargo, las influencias en el rendimiento de aprendizaje de los algoritmos de aprendizaje por refuerzo suelen comprenderse mal en la práctica.',
     (WARN, [MUST_BE_ENGLISH])),
]

@pytest.mark.parametrize("test", ABSTRACT_TESTS)
def test_abstracts(test):
    (abs, expected_result) = test
    result = metacheck.check( { ABSTRACT: abs } );
    # print( abs, result, expected_result )
    check_result(result[ABSTRACT], expected_result)

############################################################
##### Detailed tests for COMMENTS field

COMMENTS_TESTS = [
    ('',None),
    ('A comment',None),
    ('15 pages, 6 figures',None),
    ('A comment with èéêëìíîï accents',None),
    ('A comment with èéêëìíîï accents'.encode("UTF-8").decode("LATIN-1"),
     (WARN, [
         BAD_UNICODE
     ])),
    ('A comment with 普通话 Chinese',None),
    ('A comment with 普通话 Chinese'.encode("UTF-8").decode("LATIN-1"),
     (WARN, [
         BAD_UNICODE
     ])),
    # ('15 pages, 6 figures,',(HOLD,['Comments: ends with punctuation (,)'])],
    # ['15 pages, 6 figures:',(HOLD,['Comments: ends with punctuation (:)'])],
    # ['Comments: 15 pages, 6 figures',(HOLD,['Comments: starts with the word Comments, check'])],
    # ['Poster submission to AHDF',(HOLD,["Comments: contains word 'poster'"])],
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [
         CONTAINS_BAD_STRING,
     ])),            
    ('This ] is bad',
     (WARN, [UNBALANCED_BRACKETS])),
]

@pytest.mark.parametrize("test", COMMENTS_TESTS)
def test_comments(test):
    (comments, expected_result) = test
    result = metacheck.check( { COMMENTS: comments } );
    # print( comments, result )
    check_result(result[COMMENTS], expected_result)

############################################################
##### Detailed tests for REPORT-NO field

REPORT_NO_TESTS = [
    ['LANL-UR/2001-01',None],
    ['ITP 09 #1',None],
    ['NO-NUM',(HOLD,[MUST_CONTAIN_DIGITS])],
    ['12',(WARN,[TOO_SHORT])],
    ['123',(WARN,[TOO_SHORT])],
    ['1234',(HOLD,[MUST_CONTAIN_LETTERS])],
    ['12345',(HOLD,[MUST_CONTAIN_LETTERS])],
]

@pytest.mark.parametrize("test", REPORT_NO_TESTS)
def test_report_num(test):
    (report_num, expected_result) = test
    result = metacheck.check( { REPORT_NUM: report_num } );
    # print( report_num, result )
    check_result(result[REPORT_NUM], expected_result)

############################################################
##### journal_ref field checks

JREF_TESTS = [
    # ['ibid',"Journal-ref: inappropriate word: ibid"],
    ('Proceedings of the 34th "The Web Conference" (WWW 2025)', None),
    ('JACM volume 1 issue 3, Jan 2024', None),
    ('1975',
     (WARN, [TOO_SHORT])),
    ('Science 1.1',
     (WARN, [MUST_CONTAIN_YEAR])),
    ('JACM Jan 2024 DOI:10.2345/thisisnotadoi',
     (WARN, [CONTAINS_BAD_STRING])),
    ('JACM Jan 2024 DOI:10.2345/thisisnotadoi',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Accepted for publication in JACM Jan 2024',
     (WARN, [CONTAINS_BAD_STRING])),
    ('Submitted to JACM Jan 2024',
     (WARN, [CONTAINS_BAD_STRING])),
    # ['Science SPIE 1.1',"Journal-ref: submission from SPIE conference? Check for copyright issues"],
]

@pytest.mark.parametrize("test", JREF_TESTS)
def test_jrefs(test):
    jref, expected_result = test
    result = metacheck.check( { JOURNAL_REF: jref } )
    # print( jref, result )
    check_result(result[JOURNAL_REF], expected_result)

############################################################
# (related DOI?) DOI field checks

DOI_TESTS = [
    ['10.48550/arXiv.2501.18183',None],
    ['doi.org/10.48550/arXiv.2501.18183',None],
    ['doi:10.48550/arXiv.2501.18183',None],
    ['doi:22.48550/arXiv.2501.18183',None], # valid!
    ['10.485',(WARN,[TOO_SHORT])],
    ['https://doi.org/10.48550/arXiv.2501.18183',(WARN,[CONTAINS_BAD_STRING])],
    ['http://doi.org/10.48550/arXiv.2501.18183',(WARN,[CONTAINS_BAD_STRING])],
    # TODO: Should this be valid, or not?
    # ['I like doi:10.48550/arXiv.2501.18183',(WARN,[CONTAINS_BAD_STRING])],
]

@pytest.mark.parametrize("test", DOI_TESTS)
def test_doi(test):
    (doi, expected_result) = test
    result = metacheck.check( { DOI: doi } );
    # print( doi, result )
    check_result(result[DOI], expected_result)

############################################################
#

BALANCED_BRACKETS_TESTS = [
    '10.48550/arXiv.2501.18183'
    '((()))',
    '(([[{{}}]]))',
    '(({}[[]])())[]',
]

UNBALANCED_BRACKETS_TESTS = [
    'this [ is wrong',
    'this [ } wrong',
    'this [ ) wrong',
    'this ( is wrong',
    'this ( ] wrong',
    'this ( } wrong',
    'this { is wrong',
    'this { ) wrong',
    'this { ] wrong',
    'this is ) ( wrong',
    'this is } wrong',
    'this is ] [ wrong',
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
    assert( not long_word_caps("HOMESTAKE") )
    assert( not long_word_caps("THISISALONGWORD") )            
    assert( not long_word_caps("THISISALONGWORD not long NOT LONG") )
    # HOMESTAKE is a known allcaps word
    assert( not long_word_caps("THISISALONGWORD HOMESTAKE") )
    assert( not long_word_caps("THISISALONGWORD 123456789") )    
    assert( long_word_caps("THISISALONGWORD not long VERYLONGWORD") )                

# pyenv activate arxiv-base-3-11
# python -m pytest arxiv/metadata/tests/test_metacheck.py
