from dataclasses import dataclass, field
from typing import Optional

"""arXiv license definitions."""


LICENSE_ICON_BASE_URI = "/icons/licenses"
LICENSES = {
    # key is the license URI
    'http://creativecommons.org/licenses/by/4.0/': {
        'label': 'CC BY: Creative Commons Attribution',
        "short_label": "CC BY 4.0",
        'note': 'This license allows reusers to distribute, remix, adapt, and '
                'build upon the material in any medium or format, so long as '
                'attribution is given to the creator. The license allows for '
                'commercial use.',
        'order': 1,
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-4.0.png'},
    'http://creativecommons.org/licenses/by-sa/4.0/': {
        'order': 2,
        'label': 'CC BY-SA: Creative Commons Attribution-ShareAlike',
        "short_label": "CC BY-SA 4.0",
        'note': 'This license allows reusers to distribute, remix, adapt, and '
                'build upon the material in any medium or format, so long as '
                'attribution is given to the creator. The license allows for '
                'commercial use. If you remix, adapt, or build upon the '
                'material, you must license the modified material under '
                'identical terms.',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-sa-4.0.png'},
    'http://creativecommons.org/licenses/by-nc-sa/4.0/': {
        'order': 3,
        'label': 'CC BY-NC-SA: Creative Commons '
                 'Attribution-Noncommercial-ShareAlike ',
        "short_label": "CC BY-NC-SA 4.0",
        'note': 'This license allows reusers to distribute, remix, adapt, and '
                'build upon the material in any medium or format for '
                'noncommercial purposes only, and only so long as attribution '
                'is given to the creator. If you remix, adapt, or build upon '
                'the material, you must license the modified material under '
                'identical terms.',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-sa-4.0.png'},
    'http://creativecommons.org/licenses/by-nc-nd/4.0/': {
        'order': 4,
        'label': 'CC BY-NC-ND: Creative Commons '
                 'Attribution-Noncommercial-NoDerivatives',
        "short_label": "CC BY-NC-ND 4.0",
        'note': 'This license allows reusers to copy and distribute the '
                'material in any medium or format in unadapted form only, for '
                'noncommercial purposes only, and only so long as attribution '
                'is given to the creator.',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-nd-4.0.png'},
    'http://arxiv.org/licenses/nonexclusive-distrib/1.0/': {
        'label': 'arXiv.org perpetual, non-exclusive license to '
                 'distribute this article',
        "short_label": "arXiv.org perpetual non-exclusive license",
        'note': 'This license gives limited rights to arXiv to distribute the '
                'article, and limits re-use of any type from other entities '
                'or individuals.',
        'order': 5,
        'is_current': True,
    },
    'http://creativecommons.org/publicdomain/zero/1.0/': {
        'label': 'CC Zero: No Rights Reserved',
        "short_label": "CC Zero",
        'note': 'CC Zero is a public dedication tool, which allows creators '
                'to give up their copyright and put their works into the '
                'worldwide public domain. CC0 allows reusers to distribute, '
                'remix, adapt, and build upon the material in any medium or '
                'format, with no conditions.',
        'order': 6,
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/zero-1.0.png'
    },
    'http://arxiv.org/licenses/assumed-1991-2003/': {
        'label': 'Assumed arXiv.org perpetual, non-exclusive license to '
                 'distribute this article for submissions made before '
                 'January 2004',
        "short_label": "Assumed arXiv.org perpetual non-exclusive license",
        'order': 9,
        'is_current': False,
    },
    'http://creativecommons.org/licenses/by/3.0/': {
        'label': 'Creative Commons Attribution license',
        "short_label": "CC BY 3.0",
        'order': 10,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-3.0.png'
    },
    'http://creativecommons.org/licenses/by-nc-sa/3.0/': {
        'label': 'Creative Commons Attribution-Noncommercial-ShareAlike '
                 'license',
        "short_label": "CC BY-NC-SA 3.0",
        'order': 11,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-sa-3.0.png'
    },
    'http://creativecommons.org/licenses/publicdomain/': {
        'label': 'Creative Commons Public Domain Declaration',
        "short_label": "CC Zero",
        'note': '(Suitable for US government employees, for example)',
        'order': 12,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/publicdomain.png'
    }
}
NO_LICENSE_TEXT = "I do not certify that any of the above licenses apply"

ASSUMED_LICENSE_URI = "http://arxiv.org/licenses/assumed-1991-2003/"

TRANSLATED_LICENSES = {
    "http://creativecommons.org/licenses/by/3.0/": "http://creativecommons.org/licenses/by/4.0/",
    "http://creativecommons.org/licenses/by-nc-sa/3.0/": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
    "http://creativecommons.org/licenses/publicdomain/": "http://creativecommons.org/publicdomain/zero/1.0/",
}
"""Historical license to updated/current license (old URI: new URI)."""

CURRENT_LICENSES = {
    k: v
    for k, v in LICENSES.items()
    if "order" in v and "is_current" in v and v["is_current"]
}

CURRENT_LICENSE_URIS = sorted(
    CURRENT_LICENSES, key=lambda x: CURRENT_LICENSES[x]["order"]
)  # type: ignore
"""Current license URIs by display order."""


def license_for_recorded_license(recorded_uri: Optional[str]) -> str:
    """Get the license for the value recorded in the abs file.

    This represents an important encoding of policy in code:

    The submitters of articles between 1991 and 2003 aggreed to the
    assumed license. These have no license in the abs files becasue
    the authors could only submit papers if they accepted this
    license.

    After the submission system in Perl and catalyst was put into
    production 2009, the author selected from several licenses. If the
    author selected the arXiv assumed license, the abs file would have
    no license field. If the author selected a license other than the
    assumed license, it would be recorded in the .abs file in the
    field license. If the author did not select a license or sent an
    unexpected request they were shown the license page with an error
    message that they needed to select a license. It was designed to
    make it impossible for a submittion to be accepted without a
    license.  Submissions via the SWORD system required users to
    record a license for all their submissions as part of their user
    account data.

    A lack of a license in arXiv's records did not mean the author
    failed to select a license. The classic submission system was
    explicitly written to not permit submitters to submit without
    selecting a license.
    """
    if recorded_uri is None:
        return str(ASSUMED_LICENSE_URI)

    if isinstance(recorded_uri, str):
        return recorded_uri
    else:
        raise TypeError(
            "License recorded_uri must be str or None, but it was "
            f"{type(recorded_uri).__name__}"
        )


@dataclass
class License:
    """Represents an arXiv article license."""

    recorded_uri: Optional[str] = None
    """URI of a license if one is in the article record."""

    effective_uri: str = field(init=False)
    """License that is in effect.

    When the submitter uploaded this paper to arXiv, they agreed to
    arXiv using the paper under the terms of this license. This takes
    into account assumed license.
    """

    icon_uri_path: Optional[str] = field(init=False)
    """Path to license icon."""

    label: Optional[str] = field(init=False)
    """The license label."""

    def __post_init__(self) -> None:
        """Set the effective license URI."""
        self.effective_uri = license_for_recorded_license(self.recorded_uri)
        self.icon_uri_path = None
        self.label = None
        if self.effective_uri in LICENSES:
            if 'icon_uri' in LICENSES[self.effective_uri]:
                self.icon_uri_path = LICENSES[self.effective_uri]['icon_uri']
            if 'label' in LICENSES[self.effective_uri]:
                self.label = LICENSES[self.effective_uri]['label']

    def get_short_label(self) -> Optional[str]:
        """Get the short label for the license."""
        if self.effective_uri in LICENSES:
            return LICENSES[self.effective_uri].get("short_label",
                        LICENSES[self.effective_uri].get("label", "No License")
            )
        else:
            return "No License"
