"""
arXiv group, archive and category definitions.

arXiv categories are arranged in a hierarchy where there are archives
(astro-ph, cs, math, etc.) that contain subject classes (astro-ph has subject
classes CO, GA, etc.). We now use the term category to refer to any archive or
archive.subject_class that one can submit to (so hep-th and math.IT are both
categories). No subject class can be in more than one archive. However, our
scientific advisors identify some categories that should appear in more than
one archive because they bridge major subject areas. Examples include math.MP
== math-ph and stat.TH = math.ST. These are called category aliases and the
idea is that any article classified in one of the aliases categories also
appears in the other (canonical), but that most of the arXiv code for display,
search, etc. does not need to understand the break with hierarchy.

"""
from .definitions import CATEGORIES, CATEGORIES_ACTIVE, ARCHIVES, \
    ARCHIVES_ACTIVE, ARCHIVES_SUBSUMED, CATEGORY_ALIASES
from .category import Category, Archive, Group


def get_category_display(category: str, canonical: bool = True) -> str:
    """
    Get the display name of an arXiv category.

    Parameters
    ----------
    category : str
        Category identifier, e.g. ``nlin.AO``.
    canonical : bool
        If True (default) and the category is subsumed, the display name for
        the canonical category will be returned instead.

    Returns
    -------
    str
        Display name for the category, e.g. ``Adaptation and Self-Organizing
        Systems (nlin.AO)``.

    """
    if canonical:
        return Category(category).canonical.display
    return Category(category).display


def get_archive_display(archive: str, canonical: bool = True) -> str:
    """
    Get the display name of an arXiv archive.

    Parameters
    ----------
    archive : str
        Archive identifier, e.g. ``astro-ph``.
    canonical : bool
        If True (default) and the archive is subsumed, the display name for
        the canonical archive will be returned instead.

    Returns
    -------
    str
        Display name for the category, e.g. ``Astrophysics (astro-ph)``.

    """
    if canonical:
        return Archive(archive).canonical.display
    return Archive(archive).display


def get_group_display(group: str) -> str:
    """
    Get the display name of an arXiv group.

    Parameters
    ----------
    group : str
        Group identifier, e.g. ``grp_math``.

    Returns
    -------
    str
        Display name for the group, e.g. ``Mathematics (grp_math)``.

    """
    return Group(group).display
