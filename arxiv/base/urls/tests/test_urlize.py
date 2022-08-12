import unittest
from unittest import mock
from flask import Flask
from markupsafe import escape
from .. import links


def mock_url_for(endpoint, **kwargs):
    if endpoint == "abs_by_id":
        paper_id = kwargs["paper_id"]
        return f"https://arxiv.org/abs/{paper_id}"


class Id_Patterns_Test(unittest.TestCase):
    def setUp(self):
        self.app = Flask("bogus")

    def test_arxiv_ids(self):
        def find_match(txt):
            with self.app.app_context():
                ptn = links._get_pattern(links.DEFAULT_KINDS)
                return ptn.search(txt)

        self.assertIsNotNone(find_match("math/9901123"))
        self.assertIsNotNone(find_match("hep-ex/9901123"))
        self.assertIsNotNone(find_match("gr-qc/9901123"))

        self.assertIsNotNone(find_match("1202.1234"))
        self.assertIsNotNone(find_match("1202.1234v1"))
        self.assertIsNotNone(find_match("1203.12345"))
        self.assertIsNotNone(find_match("1203.12345v1"))
        self.assertIsNotNone(find_match("1203.12345v12"))

        # slightly odd but seen in comments
        self.assertIsNotNone(find_match("hep-ph/1203.12345v12"))

    def test_find_match(self):
        def find_match(txt):
            with self.app.app_context():
                ptn = links._get_pattern(links.DEFAULT_KINDS)
                return ptn.search(txt)

        self.assertIsNone(find_match("junk"))
        self.assertIsNone(find_match(""))
        self.assertIsNone(find_match(" "))

        self.assertIsNotNone(find_match("doi:10.1002/0470841559.ch1"))
        self.assertIsNotNone(find_match("doi:10.1038/nphys1170"))

        self.assertIsNotNone(find_match("http://arxiv.org"))
        self.assertIsNotNone(find_match("http://arxiv.org?something=1"))
        self.assertIsNotNone(find_match("http://arxiv.org?something=1&anohter=2"))
        self.assertIsNotNone(find_match('"http://arxiv.org"'))


class TestURLize(unittest.TestCase):
    def setUp(self):
        self.app = Flask("bogus")

    def test_dont_urlize_cats(self):
        self.assertGreater(
            len(links.CATEGORIES_THAT_COULD_BE_HOSTNAMES),
            0,
            "The links.CATEGORIES_THAT_COULD_BE_HOSTNAMES must not be empty or it will match everything",
        )

    @mock.patch(f"{links.__name__}.clickthrough")
    def test_doi(self, mock_clickthrough):
        with self.app.app_context():
            mock_clickthrough.clickthrough_url = (
                lambda url: f"http://arxiv.org/clickthrough?url={url}"
            )
            self.maxDiff = 3000
            self.assertEqual(
                links.urlize(
                    "here is a rando doi doi:10.1109/5.771073 that needs a link"
                ),
                'here is a rando doi doi:<a href="https://doi.org/10.1109/5.771073" data-doi="10.1109/5.771073" class="link-https link-external" rel="external noopener nofollow">https://doi.org/10.1109/5.771073</a> that needs a link',
            )

    def test_transform_token(self):
        # def doi_id_url_transform_token(tkn,fn):
        #     return doi_id_url_transform_token(fn, tkn)
        with self.app.app_context():
            self.assertEqual(links.urlize("", ["url"]), "")

            self.assertEqual(
                links.urlize("it is fine, chapter 234 see<xxyx,234>"),
                escape("it is fine, chapter 234 see<xxyx,234>"),
            )

            self.assertEqual(
                links.urlize("http://arxiv.org", ["url"]),
                '<a href="http://arxiv.org" class="link-internal link-http">http://arxiv.org</a>',
            )

            self.assertEqual(
                links.urlize("https://arxiv.org", ["url"]),
                '<a href="https://arxiv.org" class="link-internal link-https">https://arxiv.org</a>',
            )

            self.assertEqual(
                links.urlize("in the front http://arxiv.org oth", ["url"]),
                'in the front <a href="http://arxiv.org" class="link-internal link-http">http://arxiv.org</a> oth',
            )

            self.assertEqual(
                links.urlize(".http://arxiv.org.", ["url"]),
                '.<a href="http://arxiv.org" class="link-internal link-http">http://arxiv.org</a>.',
            )

            self.assertEqual(
                links.urlize('"http://arxiv.org"', ["url"]),
                '"<a href="http://arxiv.org" class="link-internal link-http">http://arxiv.org</a>"',
            )

            self.assertEqual(
                links.urlize('"https://arxiv.org/help"', ["url"]),
                '"<a href="https://arxiv.org/help" class="link-internal link-https">https://arxiv.org/help</a>"',
            )

    @mock.patch(f"{links.__name__}.clickthrough")
    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_urlize(self, mock_clickthrough):
        with self.app.app_context():
            mock_clickthrough.clickthrough_url.return_value = "foo"
            self.assertEqual(
                links.urlize("http://example.com/"),
                '<a href="http://example.com/" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
                "urlize (URL linking) 1/6",
            )
            self.assertEqual(
                links.urlize("https://example.com/"),
                '<a href="https://example.com/" rel="external noopener nofollow" class="link-external link-https">this https URL</a>',
                "urlize (URL linking) 2/6",
            )
            self.assertEqual(
                links.urlize("ftp://example.com/"),
                '<a href="ftp://example.com/" rel="external noopener nofollow" class="link-external link-ftp">this ftp URL</a>',
                "urlize (URL linking) 3/6",
            )

            self.assertEqual(
                links.urlize("http://projecteuclid.org/euclid.bj/1151525136"),
                '<a href="http://projecteuclid.org/euclid.bj/1151525136" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
                "urlize (URL linking) 6/6",
            )

            self.assertEqual(
                links.urlize("2448446.4710(5)"),
                "2448446.4710(5)",
                "urlize (should not match) 1/9",
            )
            self.assertEqual(
                links.urlize("HJD=2450274.4156+/-0.0009"),
                "HJD=2450274.4156+/-0.0009",
                "urlize (should not match) 2/9",
            )
            self.assertEqual(
                links.urlize("T_min[HJD]=49238.83662(14)+0.146352739(11)E."),
                "T_min[HJD]=49238.83662(14)+0.146352739(11)E.",
                "urlize (should not match) 3/9",
            )
            self.assertEqual(
                links.urlize("Pspin=1008.3408s"),
                "Pspin=1008.3408s",
                "urlize (should not match) 4/9",
            )
            self.assertEqual(
                links.urlize("2453527.87455^{+0.00085}_{-0.00091}"),
                "2453527.87455^{+0.00085}_{-0.00091}",
                "urlize (should not match) 5/9",
            )
            self.assertEqual(
                links.urlize("2451435.4353"),
                "2451435.4353",
                "urlize (should not match) 6/9",
            )

            self.assertEqual(
                links.urlize("cond-mat/97063007"),
                '<a href="https://arxiv.org/abs/cond-mat/9706300" data-arxiv-id="cond-mat/9706300" class="link-https">cond-mat/9706300</a>7',
                "urlize (should match) 7/9",
            )

            self.assertEqual(
                links.urlize("[http://onion.com/something-funny-about-arxiv-1234]"),
                '[<a href="http://onion.com/something-funny-about-arxiv-1234" rel="external noopener nofollow" class="link-external link-http">this http URL</a>]',
            )

            self.assertEqual(
                links.urlize("[http://onion.com/?q=something-funny-about-arxiv.1234]"),
                '[<a href="http://onion.com/?q=something-funny-about-arxiv.1234" rel="external noopener nofollow" class="link-external link-http">this http URL</a>]',
            )

            self.assertEqual(
                links.urlize("http://onion.com/?q=something funny"),
                '<a href="http://onion.com/?q=something" rel="external noopener nofollow" class="link-external link-http">this http URL</a> funny',
                "Spaces CANNOT be expected to be part of URLs",
            )

            self.assertEqual(
                links.urlize('"http://onion.com/something-funny-about-arxiv-1234"'),
                '"<a href="http://onion.com/something-funny-about-arxiv-1234" rel="external noopener nofollow" class="link-external link-http">this http URL</a>"',
                "Should handle URL surrounded by double quotes",
            )

            self.assertEqual(
                links.urlize("< http://example.com/1<2 ><"),
                '&lt; <a href="http://example.com/1" rel="external noopener nofollow" class="link-external link-http">this http URL</a>&lt;2 &gt;&lt;',
                "urlize (URL linking) 5/6",
            )

            self.assertEqual(
                links.urlize(
                    'Accepted for publication in A&A. The data will be available via CDS, and can be found "http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_FILAMENTS.cgi"'
                ),
                'Accepted for publication in A&amp;A. The data will be available via CDS, and can be found "<a href="http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_FILAMENTS.cgi" rel="external noopener nofollow" class="link-external link-http">this http URL</a>"',
            )

            self.assertEqual(
                links.urlize(
                    "see http://www.tandfonline.com/doi/abs/doi:10.1080/15980316.2013.860928?journalCode=tjid20"
                ),
                'see <a href="http://www.tandfonline.com/doi/abs/doi:10.1080/15980316.2013.860928?journalCode=tjid20" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
            )

            self.assertEqual(
                links.urlize("http://authors.elsevier.com/a/1TcSd,Ig45ZtO"),
                '<a href="http://authors.elsevier.com/a/1TcSd,Ig45ZtO" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
            )

        @mock.patch(f"{links.__name__}.url_for", mock_url_for)
        def test_category_id(self):
            self.assertEqual(
                links.urlize("version of arXiv.math.GR/0512484 (2011).", ["arxiv_id"]),
                'version of arXiv.<a data-arxiv-id="math.GR/0512484" href="https://arxiv.org/abs/math.GR/0512484" class="link-https">math.GR/0512484</a> (2011).',
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_parens(self):
        """ARXIVNG-250 Linkification should not choke on parentheses."""
        with self.app.app_context():
            self.assertEqual(
                links.urlize(
                    "http://www-nuclear.univer.kharkov.ua/lib/1017_3(55)_12_p28-59.pdf"
                ),
                '<a href="http://www-nuclear.univer.kharkov.ua/lib/1017_3(55)_12_p28-59.pdf" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_hosts(self):
        with self.app.app_context():
            self.assertEqual(
                links.urlize(
                    "can be downloaded from http://rwcc.bao.ac.cn:8001/swap/NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf"
                ),
                'can be downloaded from <a href="http://rwcc.bao.ac.cn:8001/swap/NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
                "Should deal with ports correctly",
            )
            self.assertEqual(
                links.urlize(
                    "images is at http://85.20.11.14/hosting/punsly/APJLetter4.2.07/"
                ),
                'images is at <a href="http://85.20.11.14/hosting/punsly/APJLetter4.2.07/" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
                "should deal with numeric IP correctly",
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_urls_with_plus(self):
        with self.app.app_context():
            self.assertEqual(
                links.urlize(
                    "http://www.fkf.mpg.de/andersen/docs/pub/abstract2004+/pavarini_02.pdf"
                ),
                '<a href="http://www.fkf.mpg.de/andersen/docs/pub/abstract2004+/pavarini_02.pdf" rel="external noopener nofollow" class="link-external link-http">this http URL</a>',
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_anchors_with_slash(self):
        with self.app.app_context():
            self.assertIn(
                'href="https://dms.sztaki.hu/ecml-pkkd-2016/#/app/privateleaderboard"',
                links.urlize(
                    "https://dms.sztaki.hu/ecml-pkkd-2016/#/app/privateleaderboard"
                ),
                "Should deal with slash in URL anchor correctly",
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_ftp(self):
        with self.app.app_context():
            self.assertEqual(
                links.urlize(
                    "7 Pages; ftp://ftp%40micrognu%2Ecom:anon%40anon@ftp.micrognu.com/pnenp/conclusion.pdf"
                ),
                '7 Pages; <a href="ftp://ftp%40micrognu%2Ecom:anon%40anon@ftp.micrognu.com/pnenp/conclusion.pdf" rel="external noopener nofollow" class="link-external link-ftp">this ftp URL</a>',
            )

    @mock.patch(f"{links.__name__}.url_for", mock_url_for)
    def test_arxiv_prefix(self):
        with self.app.app_context():
            urlized = links.urlize("see arxiv:1201.12345")
            self.assertIn('see <a ', urlized)
            self.assertIn('class="link-https"', urlized)
            self.assertIn('data-arxiv-id="1201.12345"', urlized)
            self.assertIn('href="https://arxiv.org/abs/1201.12345"', urlized)
            self.assertIn('>arXiv:1201.12345</a>', urlized)


    @mock.patch(f"{links.__name__}.clickthrough")
    def test_doi_2(self, mock_clickthrough):
        with self.app.app_context():
            mock_clickthrough.clickthrough_url = lambda x: x
            self.assertRegex(
                links.urlize("10.1088/1475-7516/2018/07/009"),
                r'<a.*href="https://.*10.1088/1475-7516/2018/07/009".*>https://doi.org/10.1088/1475-7516/2018/07/009</a>',
            )

            self.assertRegex(
                links.urlize("10.1088/1475-7516/2019/02/E02/meta"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/meta".*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>',
            )
            self.assertRegex(
                links.urlize("10.1088/1475-7516/2019/02/E02/META"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/META".*>https://doi.org/10.1088/1475-7516/2019/02/E02/META</a>',
            )
            self.assertRegex(
                links.urlize("doi:10.1088/1475-7516/2018/07/009"),
                r'<a.*href="https://.*10.1088/1475-7516/2018/07/009".*>https://doi.org/10.1088/1475-7516/2018/07/009</a>',
            )

            self.assertRegex(
                links.urlize("doi:10.1088/1475-7516/2019/02/E02/meta"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/meta".*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>',
            )
            self.assertRegex(
                links.urlize("doi:10.1088/1475-7516/2019/02/E02/META"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/META".*>https://doi.org/10.1088/1475-7516/2019/02/E02/META</a>',
            )

    @mock.patch(f"{links.__name__}.clickthrough")
    def test_double_doi(self, mock_clickthrough):
        with self.app.app_context():
            mock_clickthrough.clickthrough_url = lambda x: x
            txt = links.urlize(
                "10.1088/1475-7516/2018/07/009 10.1088/1475-7516/2019/02/E02/meta"
            )
            self.assertNotRegex(
                txt,
                r"this.*URL",
                'DOIs should not get the generic "this https URL" they should have the DOI text',
            )
            self.assertRegex(
                txt,
                r"<a.*>https://doi.org/10.1088/1475-7516/2018/07/009</a> <a.*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>",
                "Should handle two DOIs in a row correctly",
            )

    @mock.patch(f"{links.__name__}.clickthrough")
    def test_broad_doi(self, mock_clickthrough):
        with self.app.app_context():
            mock_clickthrough.clickthrough_url = lambda x: x

            broad_doi_fn = links.urlizer(["doi_field"])

            # ARXIVNG-3523 unusual DOI
            self.assertRegex(
                broad_doi_fn("21.11130/00-1735-0000-0005-146A-E"),
                r'<a.*href="https://.*21.11130.*>21.11130/00-1735-0000-0005-146A-E</a>',
            )

            self.assertRegex(
                broad_doi_fn("10.1088/1475-7516/2018/07/009"),
                r'<a.*href="https://.*10.1088/1475-7516/2018/07/009".*>https://doi.org/10.1088/1475-7516/2018/07/009</a>',
            )

            self.assertRegex(
                broad_doi_fn("10.1088/1475-7516/2019/02/E02/meta"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/meta".*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>',
            )
            self.assertRegex(
                broad_doi_fn("10.1088/1475-7516/2019/02/E02/META"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/META".*>https://doi.org/10.1088/1475-7516/2019/02/E02/META</a>',
            )
            self.assertRegex(
                broad_doi_fn("doi:10.1088/1475-7516/2018/07/009"),
                r'<a.*href="https://.*10.1088/1475-7516/2018/07/009".*>https://doi.org/10.1088/1475-7516/2018/07/009</a>',
            )

            self.assertRegex(
                broad_doi_fn("doi:10.1088/1475-7516/2019/02/E02/meta"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/meta".*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>',
            )
            self.assertRegex(
                broad_doi_fn("doi:10.1088/1475-7516/2019/02/E02/META"),
                r'<a.*href="https://.*10.1088/1475-7516/2019/02/E02/META".*>https://doi.org/10.1088/1475-7516/2019/02/E02/META</a>',
            )

            txt = broad_doi_fn(
                "10.1088/1475-7516/2018/07/009 10.1088/1475-7516/2019/02/E02/meta"
            )
            self.assertNotRegex(
                txt,
                r"this.*URL",
                'DOIs should not get the generic "this https URL" they should have the DOI text',
            )
            self.assertRegex(
                txt,
                r"<a.*>https://doi.org/10.1088/1475-7516/2018/07/009</a> <a.*>https://doi.org/10.1088/1475-7516/2019/02/E02/meta</a>",
                "Should handle two DOIs in a row correctly",
            )

            urlized_doi = broad_doi_fn(
                "10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO;2"
            )

            self.assertNotIn(
                'href="http://2.0.CO"',
                urlized_doi,
                "Should not have odd second <A> tag for DOI urlize for ao-sci/9503001 see ARXIVNG-2049",
            )

            leg_rx = r'<a.* href="https://doi.org/10.1175/1520-0469%281996%29053%3C0946%3AASTFHH%3E2.0.CO%3B2".*'
            self.assertRegex(
                urlized_doi,
                leg_rx,
                "Should handle Complex DOI for ao-sci/9503001 see ARXIVNG-2049",
            )

            # in legacy:
            # <a href="/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1175%252F1520-0469%25281996%2529053%253C0946%253AASTFHH%253E2.0.CO%253B2&amp;v=34a1af05">10.1175/1520-0469(1996)053&lt;0946:ASTFHH&gt;2.0.CO;2</a>

            # Post clickthrough on legacy goes to :
            # https://dx.doi.org/10.1175%2F1520-0469%281996%29053%3C0946%3AASTFHH%3E2.0.CO%3B2

    def test_dont_urlize_category_name(self):
        with self.app.app_context():
            urlize = links.urlizer()
            self.assertEqual(
                urlize("math.CO"),
                "math.CO",
                "category name math.CO should not get urlized",
            )
            self.assertIn(
                'href="http://supermath.co',
                urlize("supermath.co"),
                "hostname close to category name should get urlized",
            )

    def test_dont_urlize_arxiv_dot_org(self):
        with self.app.app_context():
            urlize = links.urlizer()

            self.assertNotRegex(
                urlize("something https://arxiv.org bla"),
                r"this.*URL",
                'arxiv.org should not get "this https URL" ARXIVNG-2130',
            )

            self.assertNotRegex(
                urlize("something arxiv.org bla"),
                r"this.*URL",
                'arxiv.org should not get "this https URL" ARXIVNG-2130',
            )

            self.assertRegex(
                urlize("something arXiv.org"),
                r"arXiv\.org",
                "arXiv.org should be preserved as text [ARXIVNG-2130]",
            )

            self.assertRegex(
                urlize("something arxiv.org"),
                r"arxiv\.org",
                "arXiv.org should be preserved as text [ARXIVNG-2130]",
            )
