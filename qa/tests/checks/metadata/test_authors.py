"""Tests for AuthorsAreValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, Inputs, Metadata, Result
from qa.checks.metadata.authors import AuthorsAreValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_name == name)


class TestAuthorsAreValid:
    def test_pass_normal(self):
        assert AuthorsAreValid.check("Fred Smith").passed

    def test_pass_two_authors(self):
        assert AuthorsAreValid.check("Fred Smith, Joe Bloggs").passed

    def test_pass_short_name(self):
        assert AuthorsAreValid.check("C Li").passed

    def test_pass_reversed_order(self):
        assert AuthorsAreValid.check("Li C").passed

    def test_fail_empty(self):
        assert not AuthorsAreValid.check("").passed

    def test_fail_empty_has_sub_results(self):
        result = AuthorsAreValid.check("")
        assert not sub_result(result, "not_empty").passed

    def test_warn_too_short(self):
        result = AuthorsAreValid.check("C C")
        assert result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_warn_linebreak(self):
        result = AuthorsAreValid.check("Fred Smith, \\\\ Joe Bloggs")
        assert result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_pass_single_backslash(self):
        result = AuthorsAreValid.check("Fred Smith, \\ Joe Bloggs")
        assert result.passed

    def test_warn_bad_characters(self):
        result = AuthorsAreValid.check("Fred Smith*, Joe Bloggs#, Bob Briggs^, Jill Camana@, and Rebecca MacInnon")
        assert result.passed
        assert not sub_result(result, "no_annotation_symbols").passed

    def test_warn_asterisk(self):
        result = AuthorsAreValid.check("Hsi-Sheng Goan*, Chung-Chin Jian, Po-Wen Chen")
        assert result.passed
        assert not sub_result(result, "no_annotation_symbols").passed

    def test_warn_leading_whitespace(self):
        result = AuthorsAreValid.check(" Leading Whitespace")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_trailing_whitespace(self):
        result = AuthorsAreValid.check("Trailing Whitespace ")
        assert result.passed
        assert not sub_result(result, "no_boundary_whitespace").passed

    def test_warn_multiple_spaces(self):
        result = AuthorsAreValid.check("Multiple  Spaces")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_space_before_comma(self):
        result = AuthorsAreValid.check("Fred Smith ,Joan Alter")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_warn_double_comma(self):
        result = AuthorsAreValid.check("Fred Smith, , Joan Alter")
        assert result.passed
        assert not sub_result(result, "no_extra_whitespace").passed

    def test_pass_no_space_after_comma(self):
        assert AuthorsAreValid.check("Fred Smith,Joan Alter").passed

    def test_warn_anonymous(self):
        result = AuthorsAreValid.check("Anonymous Author")
        assert result.passed
        assert not sub_result(result, "does_not_contain_anonymous").passed

    def test_warn_corresponding(self):
        result = AuthorsAreValid.check("Corresponding Author")
        assert result.passed
        assert not sub_result(result, "does_not_contain_corresponding").passed

    def test_warn_tex_dagger(self):
        result = AuthorsAreValid.check("Fred Smith\\dag, Joe Bloggs")
        assert result.passed
        assert not sub_result(result, "does_not_contain_tex_dagger").passed

    def test_warn_begins_with_author(self):
        result = AuthorsAreValid.check("Author: Fred Smith")
        assert result.passed
        assert not sub_result(result, "does_not_begin_with_author").passed

    def test_warn_begins_with_authors(self):
        result = AuthorsAreValid.check("Authors: J. Smith, Joe Bob, and Mr. Briggs")
        assert result.passed
        assert not sub_result(result, "does_not_begin_with_author").passed

    def test_warn_html(self):
        result = AuthorsAreValid.check("Person with <sup>1</sup>")
        assert result.passed
        assert not sub_result(result, "no_html_elements").passed

    def test_warn_html_br(self):
        result = AuthorsAreValid.check("Jane Smith<br/>Joe linebreaks<br />Alice Third")
        assert result.passed
        assert not sub_result(result, "no_html_elements").passed

    def test_warn_unbalanced_brackets(self):
        result = AuthorsAreValid.check("Jane Jones (Austen Nname")
        assert result.passed
        assert not sub_result(result, "all_brackets_balanced").passed

    def test_warn_unbalanced_open_paren(self):
        result = AuthorsAreValid.check("Fred Smith, (Joe Bloggs")
        assert result.passed
        assert not sub_result(result, "all_brackets_balanced").passed

    def test_warn_unbalanced_open_paren_tex(self):
        result = AuthorsAreValid.check("(T. Zaj\\k{a}c")
        assert result.passed
        assert not sub_result(result, "all_brackets_balanced").passed

    def test_warn_space_after_open_paren(self):
        result = AuthorsAreValid.check("Stefano Liberati ( SISSA, INFN; Trieste)")
        assert result.passed
        assert not sub_result(result, "no_unnecessary_space_in_parens").passed

    def test_warn_space_before_close_paren(self):
        result = AuthorsAreValid.check("Stefano Liberati (SISSA, INFN; Trieste )")
        assert result.passed
        assert not sub_result(result, "no_unnecessary_space_in_parens").passed

    def test_warn_tilde_as_hard_space(self):
        result = AuthorsAreValid.check("Fred Smith~Jones")
        assert result.passed
        assert not sub_result(result, "does_not_contain_tilde_as_hard_space").passed

    def test_warn_tilde_after_period(self):
        result = AuthorsAreValid.check("Paul R.~Archer")
        assert result.passed
        assert not sub_result(result, "does_not_contain_tilde_as_hard_space").passed

    def test_pass_escaped_tilde_accent(self):
        assert AuthorsAreValid.check("Jean Nu\\~nos").passed

    def test_warn_trailing_punctuation(self):
        result = AuthorsAreValid.check("Fred Smith,")
        assert result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_warn_trailing_punctuation_period(self):
        result = AuthorsAreValid.check("Barney Smity.")
        assert result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_warn_trailing_punctuation_suffix(self):
        result = AuthorsAreValid.check("Barney Smity III.")
        assert result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_warn_trailing_punctuation_comma(self):
        result = AuthorsAreValid.check("Guillermo A. Lemarchand,")
        assert result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_pass_et_al(self):
        assert AuthorsAreValid.check("Fred Smith et al.").passed

    def test_pass_complex_tex_names(self):
        assert AuthorsAreValid.check(
            "Ph\\`ung H\\^o Hai, Jo\\~ao Pedro dos Santos, Pham Thanh T\\^am, {\\DJ}\\`ao V\\u{a}n Thinh"
        ).passed

    def test_pass_tex_umlaut(self):
        assert AuthorsAreValid.check('M. Bonarota, J.-L. Le Gou\\"et, T. Chaneli\\`ere').passed

    def test_pass_affiliation_in_parens(self):
        assert AuthorsAreValid.check("Fred Smith (Cornell)").passed

    def test_pass_multiple_affiliations_in_parens(self):
        assert AuthorsAreValid.check("Fred Smith (Cornell), Bob Smith (MIT)").passed

    def test_pass_numbered_affiliations(self):
        assert AuthorsAreValid.check("Fred Smith (1), ((1) Cornell)").passed

    def test_pass_semicolon_in_affiliation(self):
        assert AuthorsAreValid.check(
            "Stefano Liberati (SISSA, INFN; Trieste) and Carmen Molina-Paris (Los Alamos)"
        ).passed

    def test_warn_lone_surname(self):
        result = AuthorsAreValid.check("Bloss, Adrienne and Cornish, Audie")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_lone_surname").passed

    def test_pass_collaboration(self):
        assert AuthorsAreValid.check("The ATLAS Collaboration").passed

    def test_warn_llm_standalone(self):
        result = AuthorsAreValid.check("Llama")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_in_author_list(self):
        result = AuthorsAreValid.check("Adrienne Bloss, Audie Cornish, and ChatGPT")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_chatgpt(self):
        result = AuthorsAreValid.check("Jonathan Young and ChatGPT")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_gpt4(self):
        result = AuthorsAreValid.check("GPT-4")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_gpt5(self):
        result = AuthorsAreValid.check("GPT-5")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_llm_as_firstname(self):
        # "Claude Sonnet 4" — Claude is a common name with a firstname, no LLM pattern fires
        result = AuthorsAreValid.check("Claude Sonnet 4")
        assert result.passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_claude_with_last_name(self):
        result = AuthorsAreValid.check("Claude Smith")
        assert result.passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_claude_standalone(self):
        result = AuthorsAreValid.check("Claude")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed
        assert sub_result(result, "authors_do_not_contain_lone_surname").passed

    def test_warn_llm_gemini_with_version(self):
        result = AuthorsAreValid.check("Gemini 2.5 Pro")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_llama_as_firstname(self):
        assert AuthorsAreValid.check("Joe Llama").passed

    def test_pass_llamallama_is_lone_surname_not_llm(self):
        result = AuthorsAreValid.check("Llamallama")
        assert result.passed
        assert not sub_result(result, "authors_do_not_contain_lone_surname").passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_semicolon_separator(self):
        result = AuthorsAreValid.check("Ancille Ngendakumana; Joachim Nzotungicimpaye")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_semicolon").passed

    def test_warn_semicolon_simple(self):
        result = AuthorsAreValid.check("Stefano Liberati; Carmen Molina-Paris")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_semicolon").passed

    def test_warn_bracket_in_name(self):
        result = AuthorsAreValid.check("Sylvie Roux [MIT]")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_brackets").passed

    def test_warn_number_in_html_sup(self):
        result = AuthorsAreValid.check("Person with <sup>1</sup>")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_numbers").passed

    def test_warn_number_jennifer_8_lee(self):
        result = AuthorsAreValid.check("Jennifer 8 Lee")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_numbers").passed

    def test_warn_affiliation_physics(self):
        result = AuthorsAreValid.check("Someone Smith Physics Dept")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_affiliation").passed

    def test_warn_affiliation_university(self):
        result = AuthorsAreValid.check("Fred Smith, Joe Bloggs, Univ of Hard Knocks")
        assert result.passed
        assert not sub_result(result, "author_names_do_not_contain_affiliation").passed

    def test_pass_astrophys_not_physics(self):
        # "astrophys" contains "phys" but not the word-boundary \bPhysics\b
        assert AuthorsAreValid.check(
            "C. Sivaram (1) and Kenath Arun (2) ((1) Indian Institute of Astrophysics, Bangalore, (2) Christ Junior College, Bangalore)"
        ).passed

    def test_pass_all_caps_name(self):
        assert AuthorsAreValid.check("Sylvie ROUX").passed

    def test_pass_initial_surname(self):
        assert AuthorsAreValid.check("S Roux").passed

    def test_pass_initial_only_name(self):
        assert AuthorsAreValid.check("Fred S, Joe B").passed

    def test_pass_long_author_list(self):
        assert AuthorsAreValid.check("R. T. Wicks, T. S. Horbury, C. H. K. Chen, and A. A. Schekochihin").passed

    def test_pass_and_separated(self):
        assert AuthorsAreValid.check(
            "Thomas Brettschneider and Giovanni Volpe and Laurent Helden and Jan Wehr and Clemens Bechinger"
        ).passed

    def test_all_sub_checks_run_on_empty(self):
        result = AuthorsAreValid.check("")
        assert result.results is not None
        assert len(result.results) == len(AuthorsAreValid._checks)

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AuthorsAreValid().run(Inputs())

    def test_none_authors_raises(self):
        with pytest.raises(MissingDataError):
            AuthorsAreValid().run(Inputs(metadata=Metadata(authors=None)))

    def test_result_has_check_metadata(self):
        result = AuthorsAreValid.check("Fred Smith")
        assert result.check_name == "authors_are_valid"
        assert result.check_id == 4
        assert result.check_version == "1.0.0"
        assert result.disposition == Disposition.REJECT

    def test_fail_disposition_reject(self):
        assert AuthorsAreValid.check("").disposition == Disposition.REJECT
