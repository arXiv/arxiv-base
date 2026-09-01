"""Tests for AuthorsContainsSubmitterName."""

from qa.checks.models import QaDataRegistry, Metadata
from qa.checks.submission.user import AuthorsContainsSubmitterName
from tests.factories import make_test_submit_event_info


def test_name_contained():
    # Careful: is_name1_contained_in_name2 doesn't normalize!
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["James", "Harvey"], ["James", "Harvey"])
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["James", "Harvey"], ["J", "Harvey"])
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["James", "Harvey"], ["James", "H"])
    assert not AuthorsContainsSubmitterName.is_name1_contained_in_name2(["James", "Harvey"], ["Barney", "Rubble"])
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["O", "Henry"], ["O", "Henry"])
    assert not AuthorsContainsSubmitterName.is_name1_contained_in_name2(["Sandra", "O"], ["O", "Henry"])
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["ji", "li"], ["ji", "li"])
    assert AuthorsContainsSubmitterName.is_name1_contained_in_name2(["J", "C", "D"], ["J", "C", "D"])


class TestAuthorsContainsSubmitterName:
    def test_pass_normal(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Fred Smith"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_pass_two_authors(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Fred Smith, Tom Jones"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_pass_all_short_names(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Li O"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Li O"),
                )
            )
            .passed
        )

    def test_fail_some_short_names(self):
        assert (
            not AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="James O"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Li O"),
                )
            )
            .passed
        )

    def test_fail_name_only_in_affil(self):
        assert (
            not AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Tom Jones (at Fred Smith University)"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_pass_known_collaboration(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Tom Jones for the ATLAS collaboration"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_pass_lhcb_collaboration(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Tom Jones for the LHCb collaboration"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_pass_belle_collaboration(self):
        assert (
            AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Tom Jones for the Belle Collaboration"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )

    def test_fail_unknown_collaboration(self):
        assert (
            not AuthorsContainsSubmitterName()
            .run(
                QaDataRegistry(
                    metadata=Metadata(authors="Tom Jones for the JONAS collaboration"),
                    submit_event_info=make_test_submit_event_info(submitter_name="Fred Smith"),
                )
            )
            .passed
        )
