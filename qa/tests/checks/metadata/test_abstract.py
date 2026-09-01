"""Tests for AbstractIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, QaDataRegistry, Metadata, Result
from qa.checks.metadata.abstract import AbstractIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


class TestAbstractIsValid:
    _filler = (
        " This additional discussion is included solely to satisfy the minimum length "
        "requirement for this test case and does not affect the specific behavior under examination."
    )

    def test_pass_normal(self):
        result = AbstractIsValid.check("In this work, we study aaa, bbb, and ccc and conclude ddd." + self._filler)
        assert result.passed

    def test_pass_with_formula(self):
        result = AbstractIsValid.check("About YBa$_{2}$Cu$_{3}$O$_{6.95}$" + self._filler)
        assert result.passed

    def test_pass_with_phi(self):
        result = AbstractIsValid.check("Both \\phi and \\varphi may be used" + self._filler)
        assert result.passed

    def test_pass_abstractive_prefix(self):
        result = AbstractIsValid.check("Abstractive summarization is ok" + self._filler)
        assert result.passed

    def test_pass_begin_with_brace(self):
        result = AbstractIsValid.check("\\begin{abstract}This uses some TeX\\end{abstract}" + self._filler)
        assert result.passed

    def test_pass_cite(self):
        result = AbstractIsValid.check(
            "Work \\cite{8} established a connection between the edge $3$-coloring" + self._filler
        )
        assert result.passed

    def test_pass_newline_permitted(self):
        result = AbstractIsValid.check("Newlines\nare permitted" + self._filler)
        assert result.passed

    def test_pass_newline_indent_permitted(self):
        result = AbstractIsValid.check("Work established\n a connection between the edge $3$-coloring" + self._filler)
        assert result.passed

    def test_pass_tex_linebreak_permitted(self):
        result = AbstractIsValid.check("This \\\\ is a line break" + self._filler)
        assert result.passed

    def test_pass_single_backslash(self):
        result = AbstractIsValid.check("This \\ is not a line break" + self._filler)
        assert result.passed

    def test_fail_short_html_like_tags(self):
        """Short tags like <x>/<i>/<b> aren't in NoHtmlElements' fixed list, but are still real
        tags to a parser, so does_not_contain_unacceptable_html_tags still flags them."""
        result = AbstractIsValid.check("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>" + self._filler)
        assert not result.passed
        assert sub_result(result, "no_html_elements").passed
        assert not sub_result(result, "does_not_contain_unacceptable_html_tags").passed

    def test_fail_unacceptable_html_tag(self):
        result = AbstractIsValid.check("An abstract with <script>alert(1)</script>" + self._filler)
        assert not result.passed
        assert result.disposition == Disposition.REJECT
        assert not sub_result(result, "does_not_contain_unacceptable_html_tags").passed

    def test_warn_allowed_html_tag(self):
        """<sup> is allowed by does_not_contain_unacceptable_html_tags, but is still in
        NoHtmlElements' fixed list, so it's a WARN rather than a clean pass."""
        result = AbstractIsValid.check("About $10^{-2}$ or Q<sup>2</sup>" + self._filler)
        assert not result.passed
        assert result.disposition == Disposition.WARN
        assert not sub_result(result, "no_html_elements").passed
        assert sub_result(result, "does_not_contain_unacceptable_html_tags").passed

    def test_pass_math_lt(self):
        result = AbstractIsValid.check("We also should not flag $p_1<p_2$" + self._filler)
        assert result.passed

    def test_fail_empty(self):
        result = AbstractIsValid.check("")
        assert not result.passed

    def test_fail_empty_short_circuits(self):
        result = AbstractIsValid.check("")
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_warn_too_short(self):
        result = AbstractIsValid.check("Hi")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_tex_begin_no_brace(self):
        result = AbstractIsValid.check("This \\begin foo is flagged")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_tex_begin").passed

    def test_fail_on_french(self):
        french_text = "Nous analysons le routage UAS réfléchi pour des files d'attente hétérogènes à serveurs multiples, avec des paramètres fixes et sous charge sous-critique. Le modèle déterministe utilisé est une équation différentielle ordinaire (EDO) réfléchie sur l'orthant non négatif, et non l'équation de dérive non contrainte."
        result = AbstractIsValid.check(french_text)
        assert not result.passed
        assert not sub_result(result, "is_english").passed

    def test_fail_on_russian(self):
        russian_text = "Мы анализируем маршрутизацию с использованием отраженного БПЛА для гетерогенных многосерверных очередей при фиксированных параметрах в условиях субкритической нагрузки. Детерминированным заменителем является отраженное ОДУ на неотрицательном ортанте, а не уравнение дрейфа без ограничений. Это отраженное ОДУ имеет единственное граничное равновесие, характеризуемое скалярным уравнением согласованности и представлением выпуклого потенциала; все траектории сходятся к нему."
        result = AbstractIsValid.check(russian_text)
        assert not result.passed
        assert not sub_result(result, "is_english").passed

    def test_fail_on_chinese(self):
        chinese_text = "我們在亞臨界負載及固定參數條件下，分析了異質多伺服器排隊系統中的「反射式 UAS」（Reflected UAS）路由策略。此系統的確定性替代模型並非無約束漂移方程，而是定義在非負象限上的反射型常微分方程（ODE）。"
        result = AbstractIsValid.check(chinese_text)
        assert not result.passed
        assert not sub_result(result, "is_english").passed

    def test_none_field_short_circuits(self):
        result = AbstractIsValid().run(QaDataRegistry(metadata=Metadata(abstract=None)))
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AbstractIsValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = AbstractIsValid.check("A fine abstract with enough text.")
        assert result.check_config["name"] == "abstract_is_valid"
        assert result.check_config["id"] == 300
        assert result.check_config["version"] == "1.0.0"

    def test_fail_gives_reject_disposition(self):
        assert AbstractIsValid.check("").disposition == Disposition.REJECT


class TestCleanup:
    def test_strips_leading_and_trailing_whitespace(self):
        assert AbstractIsValid.cleanup("  Leading and trailing spaces  ") == "Leading and trailing spaces"

    def test_collapses_trailing_space_before_newline(self):
        result = AbstractIsValid.cleanup("Trailing space before newline   \nNext line")
        assert result == "Trailing space before newline Next line"

    def test_preserves_paragraph_indent(self):
        text = "First paragraph.\n  Second paragraph."
        assert AbstractIsValid.cleanup(text) == text

    def test_converts_tabs_to_spaces(self):
        assert AbstractIsValid.cleanup("A\tB\tC") == "A B C"

    def test_collapses_multiple_spaces(self):
        assert AbstractIsValid.cleanup("Too    many     spaces") == "Too many spaces"

    def test_removes_trailing_tex_linebreak(self):
        assert AbstractIsValid.cleanup("This is a line \\\\") == "This is a line"

    def test_removes_non_newline_control_chars(self):
        assert AbstractIsValid.cleanup("word1\x00word2") == "word1 word2"
        assert AbstractIsValid.cleanup("word1\x0bword2") == "word1 word2"

    def test_collapses_trailing_tab_before_newline(self):
        result = AbstractIsValid.cleanup("Trailing tab before newline\t\nNext line")
        assert result == "Trailing tab before newline Next line"

    def test_strips_leading_abstract_colon_prefix(self):
        assert AbstractIsValid.cleanup("Abstract: some text") == "some text"

    def test_strips_leading_abstract_colon_prefix_case_insensitive(self):
        assert AbstractIsValid.cleanup("ABSTRACT: some text") == "some text"

    def test_does_not_strip_abstract_prefix_without_colon(self):
        assert AbstractIsValid.cleanup("Abstract some text") == "Abstract some text"

    def test_removes_space_before_comma(self):
        assert AbstractIsValid.cleanup("word , word") == "word, word"

    def test_removes_unnecessary_space_in_parens(self):
        assert AbstractIsValid.cleanup("( text )") == "(text)"
