"""Provides a convenience class for working with arXiv categories."""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from .definitions import CATEGORIES, ARCHIVES_SUBSUMED, CATEGORY_ALIASES, \
    ARCHIVES, GROUPS

class BaseTaxonomy(BaseModel):
    id: str
    full_name: str
    is_active: bool
    alt_name: Optional[str] #if part of an alias or subsumed archive pair
    _alt_canonical: Optional[str] #private, use canonical method

    @property
    def display(self) -> str:
        """
        Output the display string for a category.
        Example: Earth and Planetary Astrophysics (astro-ph.EP)
        """
        return f'{self.full_name} ({self.id})'
    
    @property
    def canonical(self) -> str:
        """
        Get the canonicalized category, if there is one.
        In the case of subsumed archives, returns the subsuming category.
        In the case of alias pairs returns the canonical category.
        """
        return self._alt_canonical if self._alt_canonical else self.id

class Group(BaseTaxonomy):
    """Represents an arXiv group--the highest (most general) taxonomy level."""
    start_year: int
    default_archive: Optional[str]
    is_test: Optional[bool]

    def get_archives(self) -> List['Archive'] :
        """creates a list of all archives withing the group"""
        return [archive for archive in ARCHIVES.values() if archive.in_group == self.id]


class Archive(BaseTaxonomy):
    """Represents an arXiv archive--the middle level of the taxonomy."""

    in_group: str
    start_date: date
    end_date: Optional[date]

    def get_group(self) -> Group:
        """Returns parent archive."""
        return GROUPS[self.in_group]
    
    def get_categories(self) -> List['Category'] :
        """creates a list of all categories withing the group"""
        return [category for category in CATEGORIES.values() if category.in_archive == self.id]

class Category(BaseTaxonomy):
    """Represents an arXiv category."""

    in_archive: str
    is_general: bool
    description: Optional[str]

    def get_archive(self) -> Archive:
        """Returns parent archive."""
        return ARCHIVES[self.in_archive]
