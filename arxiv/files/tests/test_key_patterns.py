"""Tests for latexml HTML key derivation (key_patterns.latexml_html_path)."""
from arxiv.identifier import Identifier
from arxiv.files.key_patterns import latexml_html_path


def test_new_style_keys_unchanged():
    # squashed == filename for new-style ids: the whole post-2007 corpus keeps its keys.
    assert latexml_html_path(Identifier("2401.01234v2")) == "2401.01234v2/2401.01234v2.html"
    assert latexml_html_path(Identifier("2401.01234"), version=3) == \
        "2401.01234v3/2401.01234v3.html"


def test_old_style_keys_archive_qualified():
    assert latexml_html_path(Identifier("hep-th/9711200v3")) == \
        "hep-th9711200v3/hep-th9711200v3.html"
    assert latexml_html_path(Identifier("astro-ph/9711200"), version=1) == \
        "astro-ph9711200v1/astro-ph9711200v1.html"


def test_old_style_collision_disambiguated():
    # Bare old-style filenames are per-archive sequences: hep-th/9711200 (Maldacena) and
    # astro-ph/9711200 are DIFFERENT papers that previously shared the key 9711200v1/.
    a = latexml_html_path(Identifier("hep-th/9711200"), version=1)
    b = latexml_html_path(Identifier("astro-ph/9711200"), version=1)
    assert a != b


def test_subject_class_strips_to_archive():
    # math.GT/0309136 canonicalizes to math/0309136 -> key math0309136v1/.
    assert latexml_html_path(Identifier("math.GT/0309136v1")) == \
        "math0309136v1/math0309136v1.html"


def test_extra_asset_path():
    ident = Identifier("hep-th/9711200v3/figures/fig1.png")
    assert latexml_html_path(ident) == "hep-th9711200v3/figures/fig1.png"
