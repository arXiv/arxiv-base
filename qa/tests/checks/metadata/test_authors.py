"""Tests for AuthorsAreValid."""

import pytest

from qa.checks.base import MissingDataError
from qa.checks.models import Disposition, QaDataRegistry, Metadata, Result
from qa.checks.metadata.authors import AuthorsAreValid


def sub_result(result: Result, name: str) -> Result:
    assert result.results is not None
    return next(r for r in result.results if r.check_config["name"] == name)


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

    def test_fail_empty_short_circuits(self):
        result = AuthorsAreValid.check("")
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_warn_too_short(self):
        result = AuthorsAreValid.check("C C")
        assert not result.passed
        assert not sub_result(result, "not_too_short").passed

    def test_fail_linebreak(self):
        result = AuthorsAreValid.check("Fred Smith, \\\\ Joe Bloggs")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_linebreak").passed

    def test_pass_raw_newline_without_cleanup(self):
        """A raw newline is only removed via cleanup(); check() no longer rejects it directly."""
        assert AuthorsAreValid.check("Fred Smith,\nJoe Bloggs").passed

    def test_pass_single_backslash(self):
        result = AuthorsAreValid.check("Fred Smith, \\ Joe Bloggs")
        assert result.passed

    def test_warn_bad_characters(self):
        result = AuthorsAreValid.check("Fred Smith*, Joe Bloggs#, Bob Briggs^, Jill Camana@, and Rebecca MacInnon")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_annotation_symbols").passed

    def test_warn_asterisk(self):
        result = AuthorsAreValid.check("Hsi-Sheng Goan*, Chung-Chin Jian, Po-Wen Chen")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_annotation_symbols").passed

    def test_pass_no_space_after_comma(self):
        assert AuthorsAreValid.check("Fred Smith,Joan Alter").passed

    def test_fail_anonymous(self):
        result = AuthorsAreValid.check("Anonymous Author")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_anonymous").passed

    def test_fail_corresponding(self):
        result = AuthorsAreValid.check("Corresponding Author")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_corresponding").passed

    def test_fail_tex_dagger(self):
        result = AuthorsAreValid.check("Fred Smith\\dag, Joe Bloggs")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_tex_dagger").passed

    def test_pass_begins_with_author_without_cleanup(self):
        """A leading 'author:' prefix is only stripped via cleanup(); check() does not reject it outright,
        though the unstripped prefix confuses the author parser into a spurious lone-surname warning."""
        result = AuthorsAreValid.check("Author: Fred Smith")
        assert result.disposition != Disposition.REJECT

    def test_pass_begins_with_authors_without_cleanup(self):
        """A leading 'authors:' prefix is only stripped via cleanup(); check() does not reject it outright,
        though the unstripped prefix confuses the author parser into a spurious lone-surname warning."""
        result = AuthorsAreValid.check("Authors: J. Smith, Joe Bob, and Mr. Briggs")
        assert result.disposition != Disposition.REJECT

    def test_pass_tilde_as_hard_space_without_cleanup(self):
        """A tilde hard-space is only normalized via cleanup(); check() no longer rejects it directly."""
        assert AuthorsAreValid.check("Fred Smith~Jones").passed

    def test_pass_tilde_after_period_without_cleanup(self):
        """A tilde hard-space is only normalized via cleanup(); check() no longer rejects it directly."""
        assert AuthorsAreValid.check("Paul R.~Archer").passed

    def test_pass_escaped_tilde_accent(self):
        assert AuthorsAreValid.check("Jean Nu\\~nos").passed

    def test_fail_trailing_punctuation(self):
        result = AuthorsAreValid.check("Fred Smith,")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_fail_trailing_punctuation_period(self):
        result = AuthorsAreValid.check("Barney Smity.")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_fail_trailing_punctuation_suffix(self):
        result = AuthorsAreValid.check("Barney Smity III.")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_fail_trailing_punctuation_comma(self):
        result = AuthorsAreValid.check("Guillermo A. Lemarchand,")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

    def test_fail_et_al(self):
        result = AuthorsAreValid.check("Fred Smith et al.")
        assert not result.passed
        assert not sub_result(result, "does_not_end_with_punctuation").passed

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
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_lone_surname").passed

    def test_pass_collaboration(self):
        assert AuthorsAreValid.check("The ATLAS Collaboration").passed

    def test_warn_llm_standalone(self):
        result = AuthorsAreValid.check("Llama")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_in_author_list(self):
        result = AuthorsAreValid.check("Adrienne Bloss, Audie Cornish, and ChatGPT")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_chatgpt(self):
        result = AuthorsAreValid.check("Jonathan Young and ChatGPT")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_gpt4(self):
        result = AuthorsAreValid.check("GPT-4")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_llm_gpt5(self):
        result = AuthorsAreValid.check("GPT-5")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_llm_as_firstname(self):
        # "Claude Sonnet" — Claude is a common name with a firstname, no LLM pattern fires
        result = AuthorsAreValid.check("Claude Sonnet")
        assert result.passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_claude_with_last_name(self):
        result = AuthorsAreValid.check("Claude Smith")
        assert result.passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_warn_claude_standalone(self):
        result = AuthorsAreValid.check("Claude")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed
        assert sub_result(result, "authors_do_not_contain_lone_surname").passed

    def test_warn_llm_gemini_with_version(self):
        result = AuthorsAreValid.check("Gemini 2.5 Pro")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_pass_llama_as_firstname(self):
        assert AuthorsAreValid.check("Joe Llama").passed

    def test_pass_llamallama_is_lone_surname_not_llm(self):
        """'Llamallama' is a real lone-surname warning, not an LLM-name match."""
        result = AuthorsAreValid.check("Llamallama")
        assert not result.passed
        assert not sub_result(result, "authors_do_not_contain_lone_surname").passed
        assert sub_result(result, "authors_do_not_contain_llm_author").passed

    def test_fail_semicolon_separator(self):
        result = AuthorsAreValid.check("Ancille Ngendakumana; Joachim Nzotungicimpaye")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_semicolon").passed

    def test_fail_semicolon_simple(self):
        result = AuthorsAreValid.check("Stefano Liberati; Carmen Molina-Paris")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_semicolon").passed

    def test_warn_bracket_in_name(self):
        result = AuthorsAreValid.check("Sylvie Roux [MIT]")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_brackets").passed

    def test_fail_number_in_html_sup(self):
        result = AuthorsAreValid.check("Person with <sup>1</sup>")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_numbers").passed
        assert not sub_result(result, "no_html_elements").passed

    def test_warn_number_jennifer_8_lee(self):
        result = AuthorsAreValid.check("Jennifer 8 Lee")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_numbers").passed

    def test_warn_affiliation_physics(self):
        result = AuthorsAreValid.check("Someone Smith Physics Dept")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_affiliation").passed

    def test_warn_affiliation_university(self):
        result = AuthorsAreValid.check("Fred Smith, Joe Bloggs, Univ of Hard Knocks")
        assert not result.passed
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

    def test_fail_et_al_with_period(self):
        result = AuthorsAreValid.check("Fred Smith et. al.")
        assert not result.passed
        assert not sub_result(result, "does_not_contain_et_al").passed

    def test_pass_space_before_comma_without_cleanup(self):
        """Space before a comma is only normalized via cleanup(); check() no longer rejects it directly."""
        assert AuthorsAreValid.check("Fred Smith , Joe Bloggs").passed

    def test_fail_prefix_dr(self):
        result = AuthorsAreValid.check("Dr. John Smith")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_prefix").passed

    def test_pass_prefix_dr_without_punctuation(self):
        assert AuthorsAreValid.check("Dr John Smith").passed

    def test_fail_prefix_prof(self):
        result = AuthorsAreValid.check("Prof. Jane Doe")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_prefix").passed

    def test_pass_prefix_prof_without_punctuation(self):
        assert AuthorsAreValid.check("Prof Jane Doe").passed

    def test_fail_suffix_phd(self):
        result = AuthorsAreValid.check("John Smith, PhD")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_degree_suffix").passed

    def test_fail_suffix_ieee(self):
        result = AuthorsAreValid.check("John Smith IEEE")
        assert not result.passed
        assert not sub_result(result, "author_names_do_not_contain_degree_suffix").passed

    def test_warn_all_caps(self):
        result = AuthorsAreValid.check("FRED SMITH AND JOE BLOGGS")
        assert not result.passed
        assert not sub_result(result, "not_all_caps").passed

    def test_pass_unspaced_comma_without_cleanup(self):
        """An unspaced comma is only normalized via cleanup(); check() no longer warns on it directly."""
        assert AuthorsAreValid.check("Jamie Magyar,Jonathan Young").passed

    def test_none_field_short_circuits(self):
        result = AuthorsAreValid().run(QaDataRegistry(metadata=Metadata(authors=None)))
        assert not result.passed
        assert result.results is not None
        assert len(result.results) == 1
        assert not result.results[0].passed
        assert result.results[0].disposition == Disposition.REJECT

    def test_missing_metadata_raises(self):
        with pytest.raises(MissingDataError):
            AuthorsAreValid().run(QaDataRegistry())

    def test_result_has_check_metadata(self):
        result = AuthorsAreValid.check("Fred Smith")
        assert result.check_config["name"] == "authors_are_valid"
        assert result.check_config["id"] == 200
        assert result.check_config["version"] == "1.0.0"

    def test_fail_gives_reject_disposition(self):
        assert AuthorsAreValid.check("").disposition == Disposition.REJECT


class TestCleanup:
    def test_collapses_whitespace_and_double_commas(self):
        assert AuthorsAreValid.cleanup("Fred  Smith,,  Joe Bloggs") == "Fred Smith, Joe Bloggs"

    def test_adds_space_before_opening_parenthesis(self):
        assert AuthorsAreValid.cleanup("Fred Smith(Cornell)") == "Fred Smith (Cornell)"

    def test_lowercases_and_after_word(self):
        assert AuthorsAreValid.cleanup("Fred Smith AND Joe Bloggs") == "Fred Smith and Joe Bloggs"

    def test_strips_leading_and_trailing_whitespace(self):
        assert AuthorsAreValid.cleanup("  Fred Smith  ") == "Fred Smith"

    def test_removes_control_chars(self):
        assert AuthorsAreValid.cleanup("Fred Smith\x00Joe Bloggs") == "Fred Smith Joe Bloggs"

    def test_removes_space_before_comma(self):
        assert AuthorsAreValid.cleanup("Fred Smith , Joe Bloggs") == "Fred Smith, Joe Bloggs"

    def test_adds_space_after_unspaced_comma(self):
        assert AuthorsAreValid.cleanup("Jamie Magyar,Jonathan Young") == "Jamie Magyar, Jonathan Young"

    def test_removes_unnecessary_space_in_parens(self):
        assert AuthorsAreValid.cleanup("Fred Smith ( Cornell )") == "Fred Smith (Cornell)"

    def test_strips_leading_author_colon_prefix(self):
        assert AuthorsAreValid.cleanup("Author: Fred Smith") == "Fred Smith"

    def test_strips_leading_authors_colon_prefix(self):
        assert AuthorsAreValid.cleanup("Authors: Fred Smith, Joe Bloggs") == "Fred Smith, Joe Bloggs"

    def test_does_not_strip_author_prefix_without_colon(self):
        assert AuthorsAreValid.cleanup("Author Fred Smith") == "Author Fred Smith"

    def test_converts_tilde_hard_space_to_space(self):
        assert AuthorsAreValid.cleanup("Paul R.~Archer") == "Paul R. Archer"

    def test_preserves_escaped_tilde(self):
        assert AuthorsAreValid.cleanup("Jean Nu\\~nos") == "Jean Nu\\~nos"
