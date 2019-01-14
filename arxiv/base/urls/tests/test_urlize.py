import unittest
from unittest import mock
import re

from jinja2 import Markup, escape
from .. import links


def mock_url_for(endpoint, **kwargs):
    if endpoint == 'abs_by_id':
        paper_id = kwargs['paper_id']
        return f'https://arxiv.org/abs/{paper_id}'


class Id_Patterns_Test(unittest.TestCase):

    def test_basic(self):
        links._find_match([], 'test')

        m = links._find_match([links.Matchable([], re.compile(r'test'))],
                              'test')
        self.assertIsNotNone(m)
        m0 = links.Matchable([], re.compile(r'test'))
        m1 = links.Matchable([], re.compile(r'tests'))

        m = links._find_match([m0, m1], 'test')
        self.assertIsNotNone(m)
        self.assertEqual(m[1], m0)

        m = links._find_match([m0, m1], 'tests')
        self.assertIsNotNone(m)
        self.assertEqual(m[1], m0)

        m = links._find_match([m1, m0], 'tests')
        self.assertIsNotNone(m)
        self.assertEqual(m[1], m1)

    def test_arxiv_ids(self):
        def find_match(txt):
            return links._find_match(links.dois_ids_and_urls, txt)

        self.assertIsNotNone(find_match('math/9901123'))
        self.assertIsNotNone(find_match('hep-ex/9901123'))
        self.assertIsNotNone(find_match('gr-qc/9901123'))

        self.assertIsNotNone(find_match('1202.1234'))
        self.assertIsNotNone(find_match('1202.1234v1'))
        self.assertIsNotNone(find_match('1203.12345'))
        self.assertIsNotNone(find_match('1203.12345v1'))
        self.assertIsNotNone(find_match('1203.12345v12'))

        # slightly odd but seen in comments
        self.assertIsNotNone(find_match('hep-ph/1203.12345v12'))

    def test_find_match(self):
        def find_match(txt):
            return links._find_match(links.dois_ids_and_urls, txt)

        self.assertIsNone(find_match('junk'))
        self.assertIsNone(find_match(''))
        self.assertIsNone(find_match(' '))

        self.assertIsNotNone(find_match('doi:10.1002/0470841559.ch1'))
        self.assertIsNotNone(find_match('doi:10.1038/nphys1170'))

        self.assertIsNotNone(find_match('http://arxiv.org'))
        self.assertIsNotNone(find_match('http://arxiv.org?something=1'))
        self.assertIsNotNone(
            find_match('http://arxiv.org?something=1&anohter=2')
        )
        self.assertIsNotNone(find_match('"http://arxiv.org"'))

    def test_transform_token(self):
        # def doi_id_url_transform_token(tkn,fn):
        #     return doi_id_url_transform_token(fn, tkn)

        self.assertEqual(links.urlize('', ['url']), '')

        self.assertEqual(
            links.urlize('it is fine, chapter 234 see<xxyx,234>'),
            Markup(escape('it is fine, chapter 234 see<xxyx,234>'))
        )

        self.assertEqual(links.urlize('http://arxiv.org', ['url']),
                         '<a href="http://arxiv.org">this http URL</a>')

        self.assertEqual(
            links.urlize('in the front http://arxiv.org oth', ['url']),
            'in the front <a href="http://arxiv.org">this http URL</a> oth'
        )

        self.assertEqual(
            links.urlize('.http://arxiv.org.', ['url']),
            '.<a href="http://arxiv.org">this http URL</a>.'
        )

        self.assertEqual(
            links.urlize('"http://arxiv.org"', ['url']),
            Markup('&#34;<a href="http://arxiv.org">this http URL</a>&#34;')
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_urlize(self):
        self.assertEqual(
            links.urlize('http://example.com/'),
            '<a href="http://example.com/">this http URL</a>',
            'urlize (URL linking) 1/6'
        )
        self.assertEqual(
            links.urlize('https://example.com/'),
            '<a href="https://example.com/">this https URL</a>',
            'urlize (URL linking) 2/6'
        )
        self.assertEqual(
            links.urlize('ftp://example.com/'),
            '<a href="ftp://example.com/">this ftp URL</a>',
            'urlize (URL linking) 3/6'
        )

        self.assertEqual(
            links.urlize('http://projecteuclid.org/euclid.bj/1151525136'),
            '<a href="http://projecteuclid.org/euclid.bj/1151525136">this http'
            ' URL</a>',
            'urlize (URL linking) 6/6'
        )

        self.assertEqual(links.urlize('2448446.4710(5)'), '2448446.4710(5)',
                         'urlize (should not match) 1/9')
        self.assertEqual(links.urlize('HJD=2450274.4156+/-0.0009'),
                         'HJD=2450274.4156+/-0.0009',
                         'urlize (should not match) 2/9')
        self.assertEqual(
            links.urlize('T_min[HJD]=49238.83662(14)+0.146352739(11)E.'),
            'T_min[HJD]=49238.83662(14)+0.146352739(11)E.',
            'urlize (should not match) 3/9'
        )
        self.assertEqual(links.urlize('Pspin=1008.3408s'),
                         'Pspin=1008.3408s',
                         'urlize (should not match) 4/9')
        self.assertEqual(
            links.urlize('2453527.87455^{+0.00085}_{-0.00091}'),
            '2453527.87455^{+0.00085}_{-0.00091}',
            'urlize (should not match) 5/9'
        )
        self.assertEqual(links.urlize('2451435.4353'), '2451435.4353',
                         'urlize (should not match) 6/9')

        self.assertEqual(
            links.urlize('cond-mat/97063007'),
            '<a href="https://arxiv.org/abs/cond-mat/9706300">cond-mat/9706300'
            '</a>7',
            'urlize (should match) 7/9')

        self.assertEqual(
            links.urlize(
                '[http://onion.com/something-funny-about-arxiv-1234]'
            ),
            '[<a href="http://onion.com/something-funny-about-arxiv-1234">this'
            ' http URL</a>]')

        self.assertEqual(
            links.urlize(
                '[http://onion.com/?q=something-funny-about-arxiv.1234]'
            ),
            '[<a href="http://onion.com/?q=something-funny-about-arxiv.1234">'
            'this http URL</a>]'
        )

        self.assertEqual(
            links.urlize('http://onion.com/?q=something funny'),
            '<a href="http://onion.com/?q=something">this http URL</a> funny',
            'Spaces CANNOT be expected to be part of URLs'
        )

        self.assertEqual(
            links.urlize(
                '"http://onion.com/something-funny-about-arxiv-1234"'
            ),
            Markup('&#34;<a href="http://onion.com/something-funny-about-arxiv'
                   '-1234">this http URL</a>&#34;'),
            'Should handle URL surrounded by double quotes'
        )

        self.assertEqual(links.urlize('< http://example.com/1<2 ><'),
                         '&lt; <a href="http://example.com/1">this http URL'
                         '</a>&lt;2 &gt;&lt;',
                         'urlize (URL linking) 5/6')

        self.assertEqual(
            links.urlize('Accepted for publication in A&A. The data will be'
                         ' available via CDS, and can be found "http://atla'
                         'sgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_FILAMENTS'
                         '.cgi"'),
            'Accepted for publication in A&amp;A. The data will be available v'
            'ia CDS, and can be found &#34;<a href=\"http://atlasgal.mpifr-bon'
            'n.mpg.de/cgi-bin/ATLASGAL_FILAMENTS.cgi">this http URL</a>&#34;'
        )

        self.assertEqual(
            links.urlize('see http://www.tandfonline.com/doi/abs/doi:10.108'
                         '0/15980316.2013.860928?journalCode=tjid20'),
            'see <a href="http://www.tandfonline.com/doi/abs/doi:10.1080/15980'
            '316.2013.860928?journalCode=tjid20">this http URL</a>'
        )

        self.assertEqual(
            links.urlize('http://authors.elsevier.com/a/1TcSd,Ig45ZtO'),
            '<a href="http://authors.elsevier.com/a/1TcSd,Ig45ZtO">this http'
            ' URL</a>'
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_category_id(self):
        self.assertEqual(
            links.urlize('version of arXiv.math.GR/0512484 (2011).'),
            'version of arXiv.<a href=\"https://arxiv.org/abs/math.GR/0512484'
            '\">math.GR/0512484</a> (2011).'
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_parens(self):
        self.assertEqual(
            links.urlize('http://www-nuclear.univer.kharkov.ua/lib/1017_3(55)_12_p28-59.pdf'),
            '<a href=\"http://www-nuclear.univer.kharkov.ua/lib/1017_3(55)_12_p28-59.pdf\">this http URL</a>'
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_hosts(self):
        self.assertEqual(
            links.urlize('can be downloaded from http://rwcc.bao.ac.cn:8001'
                         '/swap/NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf'),
            "can be downloaded from <a href=\"http://rwcc.bao.ac.cn:8001/swap/"
            "NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf\">this http URL</a>",
            "Should deal with ports correctly"
        )
        self.assertEqual(
            links.urlize("images is at http://85.20.11.14/hosting/punsly/AP"
                         "JLetter4.2.07/"),
            'images is at <a href="http://85.20.11.14/hosting/punsly/APJLetter'
            '4.2.07/">this http URL</a>',
            "should deal with numeric IP correctly"
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_urls_with_plus(self):
        self.assertEqual(
            links.urlize('http://www.fkf.mpg.de/andersen/docs/pub/abstract2'
                         '004+/pavarini_02.pdf'),
            "<a href=\"http://www.fkf.mpg.de/andersen/docs/pub/abstract2004+/p"
            "avarini_02.pdf\">this http URL</a>",
            "Should deal with plus in URL correctly"
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_anchors_with_slash(self):
        self.assertEqual(
            links.urlize('https://dms.sztaki.hu/ecml-pkkd-2016/#/app/privat'
                         'eleaderboard'),
            Markup("<a href=\"https://dms.sztaki.hu/ecml-pkkd-2016/#/app/priva"
                   "teleaderboard\">this https URL</a>"),
            "Should deal with slash in URL anchor correctly"
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_ftp(self):
        cmt = "7 Pages; ftp://ftp%40micrognu%2Ecom:anon%40anon@ftp.micrognu." \
              "com/pnenp/conclusion.pdf"
        self.assertEqual(
            links.urlize(cmt),
            Markup('7 Pages; <a href="ftp://ftp%40micrognu%2Ecom:anon%40anon@'
                   'ftp.micrognu.com/pnenp/conclusion.pdf">this ftp URL</a>')
        )

    @mock.patch(f'{links.__name__}.url_for', mock_url_for)
    def test_arxiv_prefix(self):
        cmt = "see arxiv:1201.12345"
        self.assertEqual(
            links.urlize(cmt),
            Markup('see <a href="https://arxiv.org/abs/1201.12345">arXiv:1201.'
                   '12345</a>')
        )
