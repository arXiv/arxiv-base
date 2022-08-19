"""Tests for Tex to UTF8 parsing."""
from unittest import TestCase

from ..tex2utf import tex2utf


class TextTex2Utf(TestCase):

    def test_tex2utf(self):
        test_str = "abc def ghijk lmnop qrs tuv wxyz 1234567890 !@# $%^ &* () _-=+"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, test_str)

        utf_out = tex2utf(test_str, greek=False)
        self.assertEqual(utf_out, test_str)

        test_str = "\\'e"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0xe9))

        test_str = "\\'E"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(
            0xc9))

        test_str = "\\'E"
        utf_out = tex2utf(test_str, greek=True)
        self.assertEqual(utf_out, chr(
            0xc9))

        test_str = "\\'E"
        utf_out = tex2utf(test_str, greek=False)
        self.assertEqual(utf_out, chr(0xc9))

        test_str = "\\'E"
        utf_out = tex2utf(test_str, False)
        self.assertEqual(utf_out, chr(0xc9))

        # single textsymbol
        test_str = '\\OE'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x0152))

        # single textsymbol followed by newline
        test_str = "\\OE\n"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x0152) + "\n")

        # test_string of textsymbols
        test_str = "\\OE\\S"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x0152) + chr(0x00a7))

        # test_string of textsymbols followed by newline
        test_str = "\\OE\\S\n"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x0152) + chr(
            0x00a7) + "\n")

        # combination of textlet and textsymbols with whitespace as separator
        test_str = "\\ddag \\OE\\S"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x2021) + chr(0x0152) + chr(
            0x00a7))

        # single greek textlet
        test_str = '\\alpha'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(
            0x03b1))

        test_str = '\\alpha'
        utf_out = tex2utf(test_str, True)
        self.assertEqual(utf_out, chr(
            0x03b1))

        test_str = '\\alpha'
        utf_out = tex2utf(test_str, False)
        self.assertEqual(utf_out, r'\alpha')

        # simple test_string of greek
        test_str = '\\alpha\\beta\\gamma'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x03b1) + chr(0x03b2) + chr(
            0x03b3))

        # test_string of greek textlet with nested curlies
        test_str = '\\alpha{\\beta{\\gamma}}'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(
            0x03b1) + '{' + chr(0x03b2) + chr(0x03b3) + '}')

        # another test_string of greek with nested curlies
        test_str = '\\alpha{\\beta{\\gamma\macro}'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'α{β{γ\\macro}')

        # use "\ " as textlet delimiter
        test_str = 'foo \\alpha\\ bar'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) +
                         ' bar')

        # use "\ " as textlet delimiter
        test_str = '\\alpha\\ \\beta{something}'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(0x03b1) + ' ' +
                         chr(0x03b2) + '{something}')

        # use "\ " as textlet delimiter
        test_str = 'foo \\OE\\ bar'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x0152) +
                         ' bar')

        # use " " as textlet delimiter
        test_str = 'foo \\alpha bar'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) + 'bar')

        # use empty "{}" as textlet delimiter
        test_str = 'foo \\alpha{}bar'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) + 'bar')

        # textlet followed by non-empty "{ +  + }"
        test_str = 'foo \\alpha{-}bar'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) +
                         '{-}bar')

        # textlet followed by underscore (for subscript)
        test_str = 'foo \\alpha_7'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) +
                         '_7')

    def test_tex2utf_underscore(self):
        # textlet followed by underscore (for subscript)
        test_str = 'foo \\alpha_\\beta_\\gamma_7'
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'foo ' + chr(0x03b1) + '_' +
                         chr(0x03b2) + '_' + chr(0x03b3) + '_7')

    # <test><args>\'E</args><func>tex2UTF</func><out>&#xc9;</out></test>
    def test_tex2utf_curly(self):
        test_str = "\\'{e}"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, chr(
            0xe9))

        # <test><args>\'{e}</args><func>tex2UTF</func><out>&#xe9;</out></test>
        # <test><args>{\'e}</args><func>tex2UTF</func><out>{&#xe9;}</out></test>

    def test_ARXIVDEV2322fixes(self):
        test_str = "ARXIVDEV-2322 \\u{A} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x102) + ' fix')

        test_str = "ARXIVDEV-2322 \\u{a} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x103) + ' fix')

        test_str = "ARXIVDEV-2322 \\u{O} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x14e) + ' fix')

        test_str = "ARXIVDEV-2322 \\u{o} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x14f) + ' fix')

        test_str = "ARXIVDEV-2322 \\k{i} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x12f) + ' fix')

        test_str = "ARXIVDEV-2322 \\v{g} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x1e7) + ' fix')

        test_str = "ARXIVDEV-2322 \\c{g} fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x123) + ' fix')

        test_str = "ARXIVDEV-2322 \\DJ  fix"
        utf_out = tex2utf(test_str)
        self.assertEqual(utf_out, 'ARXIVDEV-2322 ' + chr(0x110) + ' fix')

    def test_ARXIVOPS805(self):
        """{\aa} wasn't being converted correctly in /abs abstract field to å"""
        self.assertEqual(tex2utf("ARXIVOPS-805 \\aa  fix"),
                         'ARXIVOPS-805 å fix')

        self.assertEqual(tex2utf("ARXIVOPS-805 \\aa  fix", greek=False),
                         'ARXIVOPS-805 å fix')

        self.assertEqual(tex2utf("ARXIVOPS-805 \\aa  fix", greek=True),
                         'ARXIVOPS-805 å fix')
