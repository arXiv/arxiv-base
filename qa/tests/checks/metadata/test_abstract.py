"""Tests for AbstractIsValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, Inputs, Metadata, Result
from qa.checks.metadata.abstract import AbstractIsValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestAbstractIsValid:
    def test_pass_normal(self):
        result = AbstractIsValid.check("In this work, we study aaa, bbb, and ccc and conclude ddd.")
        assert result.passed

    def test_pass_with_formula(self):
        result = AbstractIsValid.check("About YBa$_{2}$Cu$_{3}$O$_{6.95}$")
        assert result.passed

    def test_pass_with_phi(self):
        result = AbstractIsValid.check("Both \\phi and \\varphi may be used")
        assert result.passed

    def test_pass_abstractive_prefix(self):
        result = AbstractIsValid.check("Abstractive summarization is ok")
        assert result.passed

    def test_pass_begin_with_brace(self):
        result = AbstractIsValid.check("\\begin{abstract}This uses some TeX\\end{abstract}")
        assert result.passed

    def test_pass_cite(self):
        result = AbstractIsValid.check("Work \\cite{8} established a connection between the edge $3$-coloring")
        assert result.passed

    def test_pass_newline_permitted(self):
        result = AbstractIsValid.check("Newlines\nare permitted")
        assert result.passed

    def test_pass_newline_indent_permitted(self):
        result = AbstractIsValid.check("Work established\n a connection between the edge $3$-coloring")
        assert result.passed

    def test_pass_tex_linebreak_permitted(self):
        result = AbstractIsValid.check("This \\\\ is a line break")
        assert result.passed

    def test_pass_single_backslash(self):
        result = AbstractIsValid.check("This \\ is not a line break")
        assert result.passed

    def test_pass_short_html_like_tags(self):
        result = AbstractIsValid.check("These should not be flagged as HTML: <x> <xyz> <ijk> <i> <b>")
        assert result.passed

    def test_pass_math_lt(self):
        result = AbstractIsValid.check("We also should not flag $p_1<p_2$")
        assert result.passed

    def test_fail_empty(self):
        result = AbstractIsValid.check("")
        assert not result.passed

    def test_fail_empty_has_sub_results(self):
        result = AbstractIsValid.check("")
        assert not sub_result(result, "not_empty").passed

    def test_warn_too_short(self):
        result = AbstractIsValid.check("Hi")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_begins_with_abstract(self):
        result = AbstractIsValid.check("Abstract: some text")
        assert result.passed
        assert not sub_result(result, "does_not_begin_with_abstract").passed

    def test_warn_leading_whitespace(self):
        result = AbstractIsValid.check(" This contains a leading space")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_trailing_whitespace(self):
        result = AbstractIsValid.check("This contains a trailing space ")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = AbstractIsValid.check("This contains  two spaces")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_space_before_newline(self):
        result = AbstractIsValid.check("Work established  \na connection between the edge $3$-coloring")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_empty_paragraph(self):
        result = AbstractIsValid.check("Work established\n \n\n a connection between the edge $3$-coloring")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_whitespace_only_paragraph(self):
        result = AbstractIsValid.check("Paragraphs\n \nwith only whitespace are not permitted")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_trailing_space_in_text(self):
        result = AbstractIsValid.check("Work established a connection between the edge $3$-coloring ")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_unbalanced_bracket(self):
        result = AbstractIsValid.check("This ] is bad")
        assert result.passed
        assert not sub_result(result, "all_brackets_balanced").passed

    def test_warn_control_char(self):
        result = AbstractIsValid.check("Control characters  are not permitted")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars_allow_newlines").passed

    def test_warn_tab_char(self):
        result = AbstractIsValid.check("Control characters (including tabs)\tare not permitted")
        assert result.passed
        assert not sub_result(result, "does_not_contain_control_chars_allow_newlines").passed

    def test_warn_tex_begin_no_brace(self):
        result = AbstractIsValid.check("This \\begin foo is flagged")
        assert result.passed
        assert not sub_result(result, "does_not_contain_tex_begin_env").passed

    def test_all_sub_checks_run_on_empty(self):
        result = AbstractIsValid.check("")
        assert result.results is not None
        assert len(result.results) == len(AbstractIsValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AbstractIsValid().run(Inputs())

    def test_none_abstract_raises(self):
        with pytest.raises(MissingDataError):
            AbstractIsValid().run(Inputs(metadata=Metadata(abstract=None)))

    def test_result_has_check_metadata(self):
        result = AbstractIsValid.check("A fine abstract with enough text.")
        assert result.check_name == "abstract_is_valid"
        assert result.check_id == 2
        assert result.check_version == "1.0.0"
        assert result.disposition == Disposition.REJECT

    def test_fail_disposition_reject(self):
        assert AbstractIsValid.check("").disposition == Disposition.REJECT
