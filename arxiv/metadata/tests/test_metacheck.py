
import pytest

try:
    from arxiv.metadata import FieldName
    from arxiv.metadata import Disposition
    from arxiv.metadata import metacheck

    from arxiv.metadata.metacheck import combine_dispositions
except ModuleNotFoundError:
    pytest.skip(
        """"gcld3 and/or protobuf-compile are not installed.
            To run these tests, install with:
            sudo apt install -y protobuf-compiler
            poetry install --with-dev --extras qa""", allow_module_level=True)

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

############################################################
# Helper functions for unit tests

def check_result( result, expected_result ):
    # result should be ( OK, [] ) or (HOLD, [message, message...]) or (WARN, ...)
    if expected_result is None:
        assert result[0] == OK
    else:
        assert result[0] == expected_result[0]
        assert result[1] != None
        # assert len(result[1]) == len( expected_result[1] )
        assert result[1] == expected_result[1]
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
     (HOLD, ["Title cannot be empty"])),
    ('Tiny',
     (WARN, ["Title: too short"])),
    ('a title with lowercase',
     (WARN, ["Title: starts with a lower case letter"])),
    ('aTITLE: Not So Lowercase', None),
    # NOTE: we don't check for extra spaces
    # ['  A title with leading space',"Title: leading spaces"],
    # ['A title with trailing space ',"Title: trailing spaces"],
    # ['A title  with  mutliple  spaces',"Title: multiple consecutive spaces"],
    # NOTE: Titles can end with punctuation.
    ('A title with period.', None),
    # NOTE: the test for excessive capitalization is fragile
    ('ALL CAPS TITLE',
     (WARN, ["Title: excessive capitalization"])),
    ('NOT EVEN BORDERLINE ALL CAPS TITLE',
     (WARN, ["Title: excessive capitalization"])),
    ('BORDERLINE All Caps TITLE', None),
    ('BORDERLINE ALL caps TITLE',
     (WARN, ["Title: excessive capitalization"])),
    ('This is a title WITH ONE LONG WORD CAPITALIZED', None),
    ('This is a title WITH SOME EXTRAEXTRA LONG WORDS CAPITALIZED',
     [WARN, ["Title: excessive capitalization"]]),
    # We allow some capitalized words
    ('The is a title with known long words capitalized AMANDA CHANDRA', None),
    # but digit strings don't count
    ('The is a title with 12345678 and 987654321 words not capitalized', None),
    # Check for *some* HTML entities
    ('These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>', None),
    ('Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>',
     (WARN, ['Title: contains HTML'])),
    ('A title with HTML<br/>linebreaks<br />there',
     (WARN, ['Title: contains HTML'])),
    ('Title: Something',
     (WARN, ["Title: begins with 'title'"])),
    ('This \\\\ is a line break',
     (WARN, ["Title: contains TeX line break"])),
    ('This \\ is not a line break', None),
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [
         'Title: contains TeX \\href',
         'Title: contains TeX \\url',
         'Title: contains \\emph',
         'Title: contains \\uline',
         'Title: contains \\textbf',
         'Title: contains \\texttt',
         'Title: contains unnecessary escape: \\#',
         'Title: contains unnecessary escape: \\%',
     ])),
]

@pytest.mark.parametrize("test", TITLE_TESTS)
def test_titles(test):
    title, expected_result = test
    result = metacheck.check( { TITLE: title } );
    check_result(result[TITLE], expected_result)

############################################################
##### Detailed tests for AUTHORS field

AUTHORS_TESTS = [
    ('Fred Smith', None),
    ('Fred Smith, Joe Bloggs', None),
    # We don't check for ellipsis, but
    # ('Fred Smith, Joe Bloggs, ...',
    #  (WARN, ["Authors: ends with punctuation"])),
    ('Fred Smith, \\ Joe Bloggs', None ),
    ('Fred Smith, \\\\ Joe Bloggs',
     (WARN, ["Authors: contains TeX line break"])),
    ('Fred Smith*, Joe Bloggs#, Bob Briggs^, Jill Camana@, and Rebecca MacInnon',
     (WARN, [
         "Authors: contains bad character '*'",
         "Authors: contains bad character '#'",
         "Authors: contains bad character '^'",
         "Authors: contains bad character '@'",
     ])),
    (' Jane  Austen ',
     (WARN, [
         "Authors: leading whitespace",
         "Authors: trailing whitespace",
         "Authors: excess whitespace",
     ])),
    ('Jane Jones (Austen Nname',
     (WARN, ["Authors: unbalanced brackets"])),
    # ('Fred Smith(University), Joe Bloggs',"Authors: missing spaces around parenthesis"),
    ('Martha Raddatz , Ayesha Rascoe',
     (WARN, ["Authors: whitespace before comma"])),
    # ('Fred Smith & Joe Bloggs',"Authors: possibly inappropriate ampersand"),
    ('Person with <sup>1</sup>',
     (WARN, ['Authors: contains HTML',
             # 'Authors: no caps in name',
             'Authors: name should not contain digits',
             ])),
    ('Jane Smith<br/>Joe linebreaks<br />Alice Third',
     (WARN, ['Authors: contains HTML'])),
    ('C. Sivaram (1) and Kenath Arun (2) ((1) Indian Institute of Astrophysics, Bangalore, (2) Christ Junior College, Bangalore)', None), # should not flag physics in astrophys as inappropriate
    ('Sylvie Roux', None),
    ('S Roux', None),
    ('Jaganathan SR', None),
    ('Sylvie ROUX', None),      # ?
    ('S ROUX', None),
    ('SYLVIE ROUX',
     (WARN, ["Author name is in all caps"])),
    ('Sylvie roux', None),      # ?
    ('sylvie roux',
     (WARN, ["Authors: no caps in name"])),
    ('Sylvie Roux [MIT]',
     (WARN, ["Authors: name should not contain brackets"])),
    ('Jennifer 8 Lee',          # An actual name
     (WARN, ["Authors: name should not contain digits"])),
    ('Someone Smith Physics Dept',
     (WARN, [
         'Authors: name should not contain Physics',
         'Authors: name should not contain Dept'])),
    ('Smith',
     (WARN, ['Authors: lone surname'])),
    ('Fred Smith, Bloggs',
     # (WARN, ['Authors: only surname? Bloggs'])),
     (WARN, ['Authors: lone surname'])),
    ('Author: Fred Smith',
     (WARN, ["Authors: begins with 'author'"])),
    ('Authors: J. Smith, Joe Bob, and Mr. Briggs',
     (WARN, ["Authors: begins with 'authors'"])),
    ('Fred Smith (1), ((1) Cornell)', None),
    # ('Fred Smith(1), ((1) Cornell)','Authors: missing spaces around parenthesis'),
    # ('Fred Smith (1), ((1)Cornell)','Authors: missing spaces around parenthesis'),
    ('Fred Smith (Cornell)', None),
    ('Fred Smith (Cornell), Bob Smith (MIT)', None),
    ('Hsi-Sheng Goan*, Chung-Chin Jian, Po-Wen Chen',
     (WARN, ["Authors: contains bad character '*'"])),
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
     (WARN, ["Authors: ends with punctuation"])),
    # ('Ralf Sch\\"utzhold, William G.~Unruh',"Authors: tilde as hard space?"),
    ('Jean Nu\\~nos', None),
    # NOTE: The tests below require parsing the author string
    # NOTE: the author parser really messes up here.
    ('Fred Smith B.S., Joe Bloggs',
     (WARN, ["Author: found initial not surname"])), # ["Authors: initials after surname?"])),
    # ('Fred Smith, Joe Bloggs et al',"Authors: et al punctuation"),
    # ('Fred Smith \'and\' Joe Bloggs',"Authors: has literal quoted 'and' in it (change to plain and?)"),
    ('Fred Smith, (Joe Bloggs',
     (WARN, ["Authors: unbalanced brackets"])),
    # ('Fred Smith, 1040 West Addison',"Authors: postal address?"),
    ## ('UNIV of Hard Knocks',"Authors: uppercase surname or incorrectly formatted institution"),
    ('Fred Smith, Joe Bloggs, Univ of Hard Knocks',
     (WARN, ["Authors: name should not contain Univ"])),
    ('Adrienne Bloss, Audie Cornish, and ChatGPT',
     (WARN, [
         "Authors: lone surname",
         "Authors: name should not contain chatgpt",
     ])),
    # ('Paul R.~Archer', "Authors: tilde as hard space?"),
    # "Authors: includes semicolon not in affiliation, comma intended?"
    ('Ancille Ngendakumana; Joachim Nzotungicimpaye',
     (WARN, ["Authors: name should not contain ;"])),
    ('Stefano Liberati (SISSA, INFN; Trieste), Carmen Molina-Paris (Los Alamos)', None),
    # ('A.N.~Author, O K Author','Authors: tilde as hard space?'),
    ('T. L\\"u', None),
    ('T. Cs\\"org\\H{o}', None),
    ('T. Y{\\i}ld{\\i}z', None),
    ('T. Zaj\\k{a}c', None),
    ('(T. Zaj\\k{a}c',
     (WARN, ["Authors: unbalanced brackets"])),
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
     (WARN, ["Abstract: begins with 'abstract'"])),
    # ['  abstract : here  ',"Abstract: starts with the word Abstract, remove"],
    ('These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>', None),
    # ['Factor Ratio to Q<sup>2</sup> = 8.5 GeV<sup>2</sup>','Abstract: HTML elements: <sup> </sup> <sup> </sup>'],
    # ['With HTML<br/>linebreaks<br />there','Abstract: HTML elements: <br/> <br />'],
    ('Some words\\\\\\\\ more words',
     (WARN, ['Abstract: contains TeX line break'])),
    # (MathJax now handles "$3$-coloring")
    ('Work \\cite{8} established a connection between the edge $3$-coloring', None),
    # Not yet:
    # ('he abstract is sometimes missing a first letter, warn if starts with lower',
    # (WARN, ['Abstract: starts with lower case']
    # ["Lone periods should not be allowed.\\n.\\n",'Abstract: lone period, remove or it will break the mailing!'],
    ('This \\ is not a line break', None),
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [
         'Abstract: contains TeX \\href',
         'Abstract: contains TeX \\url',
         'Abstract: contains \\emph',
         'Abstract: contains \\uline',
         'Abstract: contains \\textbf',
         'Abstract: contains \\texttt',
         'Abstract: contains unnecessary escape: \\#',
         'Abstract: contains unnecessary escape: \\%',
     ])),
    ('This ] is bad',
     (WARN, ['Abstract: unbalanced brackets'])),
    ('Учењето со засилување е разноврсна рамка за учење за решавање на сложени задачи од реалниот свет. Конечно, разговараме за отворените предизвици на техниките за анализа за RL алгоритми.',
     (WARN, ['Abstract does not appear to be English'])),
    ('El aprendizaje por refuerzo es un marco versátil para aprender a resolver tareas complejas del mundo real. Sin embargo, las influencias en el rendimiento de aprendizaje de los algoritmos de aprendizaje por refuerzo suelen comprenderse mal en la práctica.',
     (WARN, ['Abstract does not appear to be English'])),
]

@pytest.mark.parametrize("test", ABSTRACT_TESTS)
def test_abstracts(test):
    (abs, expected_result) = test
    result = metacheck.check( { ABSTRACT: abs } );
    # print( abs, result )
    check_result(result[ABSTRACT], expected_result)

############################################################
##### Detailed tests for COMMENTS field

COMMENTS_TESTS = [
    ('',None),
    ('A comment',None),
    ('15 pages, 6 figures',None),
    # ('15 pages, 6 figures,',(HOLD,['Comments: ends with punctuation (,)'])],
    # ['15 pages, 6 figures:',(HOLD,['Comments: ends with punctuation (:)'])],
    # ['Comments: 15 pages, 6 figures',(HOLD,['Comments: starts with the word Comments, check'])],
    # ['Poster submission to AHDF',(HOLD,["Comments: contains word 'poster'"])],
    ('Don\'t use \\href{...}, \\url{...}, \\emph, \\uline, \\textbf, \\texttt, \\%, or \\#: Something',
     (WARN, [
         'Comments: contains TeX \\href',
         'Comments: contains TeX \\url',
         'Comments: contains \\emph',
         'Comments: contains \\uline',
         'Comments: contains \\textbf',
         'Comments: contains \\texttt',
         'Comments: contains unnecessary escape: \\#',
         'Comments: contains unnecessary escape: \\%',
     ])),
    ('This ] is bad',
     (WARN, ['Comments: unbalanced brackets'])),
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
    ['NO-NUM',(HOLD,["Report-no: no digits"])],
    ['12',(HOLD,["Report-no: too short"])],
    ['123',(HOLD,["Report-no: too short"])],
    ['1234',(HOLD,["Report-no: no letters"])],
    ['12345',(HOLD,["Report-no: no letters"])],
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
     (WARN, ["jref: too short"])),
    ('Science 1.1',
     (WARN, ["jref: missing year"])),
    ('JACM Jan 2024 DOI:10.2345/thisisnotadoi',
     (WARN, ["jref: contains DOI"])),
    ('JACM Jan 2024 DOI:10.2345/thisisnotadoi',
     (WARN, ["jref: contains DOI"])),
    ('Accepted for publication in JACM Jan 2024',
     (WARN, ["jref: contains 'accepted'"])),
    ('Submitted to JACM Jan 2024',
     (WARN, ["jref: contains 'submitted'"])),
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
    ['10.485',(WARN,["doi: too short"])],
    ['https://doi.org/10.48550/arXiv.2501.18183',(WARN,["doi: contains https:"])],
    ['http://doi.org/10.48550/arXiv.2501.18183',(WARN,["doi: contains http:"])],
    ['I like doi:10.48550/arXiv.2501.18183',(WARN,["doi: contains doi:"])],
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

# pyenv activate arxiv-base-3-11
# python -m pytest arxiv/metadata/tests/test_metacheck.py
