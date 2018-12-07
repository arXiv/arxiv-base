"""Provides a convenience class for working with arXiv categories."""

from .definitions import CATEGORIES, ARCHIVES_SUBSUMED, CATEGORY_ALIASES, \
    ARCHIVES


class Category(object):
    """Represents an arXiv category."""

    def __init__(self, category_id: str) -> None:
        """Initialize a :class:`.Category` with a category ID."""
        if category_id not in CATEGORIES:
            raise ValueError('No such category')
        self.category_id = category_id

    @property
    def name(self) -> str:
        """Get the full category name."""
        if self.category_id in CATEGORIES:
            return CATEGORIES[self.category_id]['name']
        return None

    @property
    def canonical(self) -> 'Category':
        """Get the canonicalized category, if there is one."""
        if self.category_id in ARCHIVES_SUBSUMED:
            return Category(category_id=ARCHIVES_SUBSUMED[self.category_id])
        return self

    @property
    def display(self) -> str:
        """
        String to use in display of a category.

        Examples
        --------
        Earth and Planetary Astrophysics (astro-ph.EP)
        """
        if self.category_id in CATEGORIES:
            catname = CATEGORIES[self.category_id]['name']
            return f'{catname} ({self.category_id})'
        parts = self.category_id.split('.', 2)
        if len(parts) == 2:    # Has subject.
            (archive, _) = parts
            if archive in ARCHIVES:
                archive_name = ARCHIVES[archive]['name']
                return f'{archive_name} ({self.category_id})'
        return self.category_id

    def unalias(self) -> 'Category':
        """Follow any EQUIV or SUBSUMED to get the current category."""
        if self.category_id in CATEGORY_ALIASES:
            return Category(CATEGORY_ALIASES[self.category_id])
        if self.category_id in ARCHIVES_SUBSUMED:
            return Category(ARCHIVES_SUBSUMED[self.category_id])
        return self
