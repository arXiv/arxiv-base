"""Provides a convenience class for working with arXiv categories."""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

class BaseTaxonomy(BaseModel):
    id: str
    full_name: str
    is_active: bool
    alt_name: Optional[str] #any other name the category may be known as (like if part of an alias or subsumed archive pair)
    
    @property
    def canonical(self) -> str:
        """
        Get the canonicalized category, if there is one.
        In the case of subsumed archives, returns the subsuming category.
        In the case of alias pairs returns the canonical category.
        """
        from .definitions import ARCHIVES_SUBSUMED, CATEGORY_ALIASES
        
        if self.alt_name:
            if self.id in CATEGORY_ALIASES.keys():
                return CATEGORY_ALIASES[self.id]
            elif self.id in ARCHIVES_SUBSUMED.keys():
                return ARCHIVES_SUBSUMED[self.id]

        return self.id
    
    def display(self, canonical: bool = True) -> str:
        """
        Output the display string for a category.
        If canonical, always display the canonical name
        Example: Earth and Planetary Astrophysics (astro-ph.EP)
        """
        from .definitions import CATEGORIES,ARCHIVES, GROUPS
        if not canonical:
            return f'{self.full_name} ({self.id})'
        else:
            name=self.canonical 
            if name==self.id:
                return f'{self.full_name} ({self.id})'
            elif name in CATEGORIES.keys():
                item=CATEGORIES[name]
                return f'{item.full_name} ({item.id})'
            elif name in ARCHIVES.keys():#will never happen with taxonomy as of 2024
                item=ARCHIVES[name]
                return f'{item.full_name} ({item.id})'
            elif name in GROUPS.keys(): #will never happen with taxonomy as of 2024
                item=GROUPS[name]
                return f'{item.full_name} ({item.id})'

class Group(BaseTaxonomy):
    """Represents an arXiv group--the highest (most general) taxonomy level."""
    start_year: int
    default_archive: Optional[str]
    is_test: Optional[bool]

    def get_archives(self) -> List['Archive'] :
        """creates a list of all archives withing the group"""
        from .definitions import ARCHIVES
        return [archive for archive in ARCHIVES.values() if archive.in_group == self.id]

class Archive(BaseTaxonomy):
    """Represents an arXiv archive--the middle level of the taxonomy."""

    in_group: str
    start_date: date
    end_date: Optional[date]

    def get_group(self) -> Group:
        """Returns parent archive."""
        from .definitions import GROUPS
        return GROUPS[self.in_group]
    
    def get_categories(self) -> List['Category'] :
        """creates a list of all categories withing the group"""
        from .definitions import CATEGORIES,ARCHIVES, GROUPS
        return [category for category in CATEGORIES.values() if category.in_archive == self.id]

class Category(BaseTaxonomy):
    """Represents an arXiv category."""

    in_archive: str
    is_general: bool
    description: Optional[str]

    def get_archive(self) -> Archive:
        """Returns parent archive."""
        from .definitions import ARCHIVES
        return ARCHIVES[self.in_archive]
