"""Provides a convenience class for working with arXiv categories."""

from .definitions import CATEGORIES, ARCHIVES_SUBSUMED, CATEGORY_ALIASES, \
    ARCHIVES, GROUPS


class Category(str):
    """Represents an arXiv category."""

    lookup = CATEGORIES

    @property
    def id(self) -> str:
        """Short name for category ID."""
        return self

    @property
    def name(self) -> str:
        """Get the full category name."""
        if self in self.lookup:
            return str(self.lookup[self]['name'])
        raise ValueError('No such category')

    @property
    def canonical(self) -> 'Category':
        """Get the canonicalized category, if there is one."""
        if self in CATEGORY_ALIASES:
            return Category(CATEGORY_ALIASES[self])
        if self in ARCHIVES_SUBSUMED:
            return Category(ARCHIVES_SUBSUMED[self])
        return self

    @property
    def display(self) -> str:
        """
        Output the display string for a category.

        Examples
        --------
        Earth and Planetary Astrophysics (astro-ph.EP)

        """
        if self in self.lookup:
            catname = self.lookup[self]['name']
            return f'{catname} ({self})'

        parts = self.split('.', 2)
        if len(parts) == 2:    # Has subject.
            (archive, _) = parts
            if archive in ARCHIVES:
                archive_name = ARCHIVES[archive]['name']
                return f'{archive_name} ({archive})'
        return self

    def unalias(self) -> 'Category':
        """Follow any EQUIV or SUBSUMED to get the current category."""
        if self in CATEGORY_ALIASES:
            return Category(CATEGORY_ALIASES[self])
        if self in ARCHIVES_SUBSUMED:
            return Category(ARCHIVES_SUBSUMED[self])
        return self


class Archive(Category):
    """Represents an arXiv archive--the middle level of the taxonomy."""

    lookup = ARCHIVES


class Group(Category):
    """Represents an arXiv group--the highest (most general) taxonomy level."""

    lookup = GROUPS
