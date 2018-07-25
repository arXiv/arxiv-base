"""arXiv license definitions."""


LICENSE_ICON_BASE_URI = '/icons/licenses'
LICENSES = {
    # key is the license URI
    'http://arxiv.org/licenses/nonexclusive-distrib/1.0/': {
        'label': 'arXiv.org perpetual, non-exclusive license to '
                 'distribute this article',
        'note': '(Minimal rights required by arXiv.org. Select this '
                'unless you understand the implications of other '
                'licenses)',
        'order': 1,
        'is_current': True,
    },
    'http://creativecommons.org/licenses/by/4.0/': {
        'label': 'Creative Commons Attribution license',
        'order': 5,
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-4.0.png'},

    'http://creativecommons.org/licenses/by-sa/4.0/': {
        'order': 6,
        'label': 'Creative Commons Attribution-ShareAlike license',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-sa-4.0.png'},

    'http://creativecommons.org/licenses/by-nc-sa/4.0/': {
        'order': 7,
        'label': 'Creative Commons Attribution-Noncommercial-ShareAlike '
                 'license',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-sa-4.0.png'},

    'http://creativecommons.org/publicdomain/zero/1.0/': {
        'label': 'Creative Commons Public Domain Declaration',
        'order': 8,
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/zero-1.0.png'
    },

    'http://arxiv.org/licenses/assumed-1991-2003/': {
        'label': 'Assumed arXiv.org perpetual, non-exclusive license to '
                 'distribute this article for submissions made before '
                 'January 2004',
        'order': 9,
        'is_current': False,
    },

    'http://creativecommons.org/licenses/by/3.0/': {
        'label': 'Creative Commons Attribution license',
        'order': 2,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-3.0.png'
    },

    'http://creativecommons.org/licenses/by-nc-sa/3.0/': {
        'label': 'Creative Commons Attribution-Noncommercial-ShareAlike '
                 'license',
        'order': 3,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-sa-3.0.png'
    },
    'http://creativecommons.org/licenses/publicdomain/': {
        'label': 'Creative Commons Public Domain Declaration',
        'note': '(Suitable for US government employees, for example)',
        'order': 4,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/publicdomain.png'
    }
}
NO_LICENSE_TEXT = 'I do not certify that any of the above licenses apply'

ASSUMED_LICENSE_URI = 'http://arxiv.org/licenses/assumed-1991-2003/'

TRANSLATED_LICENSES = {
    'http://creativecommons.org/licenses/by/3.0/':
    'http://creativecommons.org/licenses/by/4.0/',
    'http://creativecommons.org/licenses/by-nc-sa/3.0/':
    'http://creativecommons.org/licenses/by-nc-sa/4.0/',
    'http://creativecommons.org/licenses/publicdomain/':
    'http://creativecommons.org/publicdomain/zero/1.0/'
}
"""Historical license to updated/current license (old URI: new URI)."""

CURRENT_LICENSES = {
    k: v for k, v in LICENSES.items()
    if 'order' in v and 'is_current' in v and v['is_current']
}

CURRENT_LICENSE_URIS = \
    sorted(CURRENT_LICENSES, key=lambda x: CURRENT_LICENSES[x]['order'])
"""Current license URIs by display order."""
