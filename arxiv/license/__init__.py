"""arXiv license definitions."""


LICENSE_ICON_BASE_URI = '/icons/licenses'
LICENSES = {
    # key is the license URI
    'http://creativecommons.org/licenses/by/4.0/': {
        'label': 'CC BY: Creative Commons Attribution',
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
        'note': 'This license allows reusers to copy and distribute the '
                'material in any medium or format in unadapted form only, for '
                'noncommercial purposes only, and only so long as attribution '
                'is given to the creator.',
        'is_current': True,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-nd-4.0.png'},

    'http://arxiv.org/licenses/nonexclusive-distrib/1.0/': {
        'label': 'arXiv.org perpetual, non-exclusive license to '
                 'distribute this article',
        'note': 'This license gives limited rights to arXiv to distribute the '
                'article, and limits re-use of any type from other entities '
                'or individuals.',
        'order': 5,
        'is_current': True,
    },

    'http://creativecommons.org/publicdomain/zero/1.0/': {
        'label': 'CC Zero: No Rights Reserved',
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
        'order': 9,
        'is_current': False,
    },

    'http://creativecommons.org/licenses/by/3.0/': {
        'label': 'Creative Commons Attribution license',
        'order': 10,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-3.0.png'
    },

    'http://creativecommons.org/licenses/by-nc-sa/3.0/': {
        'label': 'Creative Commons Attribution-Noncommercial-ShareAlike '
                 'license',
        'order': 11,
        'is_current': False,
        'icon_uri': f'{LICENSE_ICON_BASE_URI}/by-nc-sa-3.0.png'
    },
    'http://creativecommons.org/licenses/publicdomain/': {
        'label': 'Creative Commons Public Domain Declaration',
        'note': '(Suitable for US government employees, for example)',
        'order': 12,
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
