"""Checks the Legacy* ("twice cooked" utf8) columns across all of arxiv.db.models. No database needed.
"""
import pytest

import arxiv.db.models  # noqa: F401   (register models)
from arxiv.db import metadata
from arxiv.db.column_types import LegacyUtf8Mixin, LegacyUtf8TooLong, legacy_utf8_decode, legacy_utf8_encode
from arxiv.db.legacy_utf8_table import check_legacy_utf8_tables
from arxiv.db.models import Submission

# arxiv-lib lib/arXiv/Schema/Result/Submission.pm: utf8_columns. All are utf8mb3 in production.
LEGACY_SUBMISSION_COLUMNS = {
    "submitter_name", "submitter_email", "title", "authors", "comments", "report_num",
    "msc_class", "acm_class", "journal_ref", "doi", "abstract",
}

SAMPLES = [
    "ASCII only",
    "Johannes Bürger",
    "Łukasz",                       # UTF-8 C5 81: 0x81 is undefined in cp1252
    "Oana-Maria-Cătălina Crișan",
    "日本語",
    "\U0001F600",                   # 4-byte UTF-8
    "Müller – “quoted” €",
]


def test_legacy_columns_are_only_in_utf8_tables() -> None:
    """Applying the double encoding to a latin1 (or undeclared) table would corrupt its data."""
    assert check_legacy_utf8_tables(metadata) == []


def test_submission_legacy_columns_match_perl() -> None:
    """Exactly the columns Perl double-encodes; the latin1 ones (proxy, license, ...) stay plain."""
    legacy = {c.name for c in Submission.__table__.columns if isinstance(c.type, LegacyUtf8Mixin)}
    assert legacy == LEGACY_SUBMISSION_COLUMNS


@pytest.mark.parametrize("sample", SAMPLES)
def test_encode_decode_round_trip(sample: str) -> None:
    assert legacy_utf8_decode(legacy_utf8_encode(sample)) == sample


def test_encode_matches_legacy_storage() -> None:
    assert legacy_utf8_encode("Bürger") == "BÃ¼rger"      # C3 BC
    assert legacy_utf8_encode("Łukasz") == "Å\u0081ukasz"      # C5 81, 0x81 -> U+0081


@pytest.mark.parametrize("stored", ["Müller", "Oana-Maria-Cătălina Crisan", "C\\u{a}t\\u{a}lina",
                                    "Ã(", "end Ã"])
def test_decode_keeps_what_is_not_double_encoded(stored: str) -> None:
    """Single-encoded text, TeX, and invalid or cut-off sequences come back as stored."""
    assert legacy_utf8_decode(stored) == stored


def test_decode_mixed_value_decodes_where_it_can() -> None:
    """Double-encoded text next to a stray U+FFFD: the double-encoded part still decodes, and
    re-encoding the result gives a fully double-encoded value instead of a third layer."""
    stored = "BÃ¼rger �"
    assert legacy_utf8_decode(stored) == "Bürger �"
    assert legacy_utf8_decode(legacy_utf8_encode(legacy_utf8_decode(stored))) == "Bürger �"


def test_too_long_once_encoded_is_refused_on_assignment() -> None:
    """VARCHAR(64) counts characters after double encoding: 21 CJK characters fit, 22 do not."""
    sub = Submission(submitter_name="张" * 21, submitter_email="x" * 64)
    with pytest.raises(LegacyUtf8TooLong) as err:
        sub.submitter_name = "张" * 22
    assert err.value.column == "arXiv_submissions.submitter_name"
    assert (err.value.length, err.value.encoded_length) == (64, 66)
    assert sub.submitter_name == "张" * 21
