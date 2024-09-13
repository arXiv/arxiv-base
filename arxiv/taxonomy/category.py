"""Provides a convenience class for working with arXiv categories."""
from typing import Optional, List, Union, Tuple
from datetime import date
from pydantic import BaseModel

class BaseTaxonomy(BaseModel):
    id: str
    full_name: str
    is_active: bool
    alt_name: Optional[str] #any other name the category may be known as (like if part of an alias or subsumed archive pair)
    
    @property
    def canonical_id(self) -> str:
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
        if self.id.startswith("bad-arch") or self.id=="grp_bad":
            return self.full_name
        elif not canonical:
            return f'{self.full_name} ({self.id})'
        else:
            name=self.canonical_id 
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

    def __eq__(self, other):
        return self.id == other.id and self.__class__ == other.__class__

    def __hash__(self):
        return hash((self.__class__, self.id))

class Group(BaseTaxonomy):
    """Represents an arXiv group--the highest (most general) taxonomy level."""
    start_year: int
    default_archive: Optional[str]
    is_test: Optional[bool]

    def get_archives(self, include_inactive: bool = False) -> List['Archive'] :
        """creates a list of all archives withing the group. By default only includes active archives"""
        from .definitions import ARCHIVES
        if include_inactive:
            return [archive for archive in ARCHIVES.values() if archive.in_group == self.id]
        else:
            return [archive for archive in ARCHIVES.values() if archive.in_group == self.id and archive.is_active]

class Archive(BaseTaxonomy):
    """Represents an arXiv archive--the middle level of the taxonomy."""

    in_group: str
    start_date: date
    end_date: Optional[date]

    def get_group(self) -> Group:
        """Returns parent archive."""
        from .definitions import GROUPS
        return GROUPS[self.in_group]
    
    def get_categories(self, include_inactive: bool =False) -> List['Category'] :
        """creates a list of all categories withing the group. By default only includes active categories"""
        from .definitions import CATEGORIES
        if include_inactive:
            return [category for category in CATEGORIES.values() if category.in_archive == self.id]
        else:
            return [category for category in CATEGORIES.values() if category.in_archive == self.id and category.is_active]

    def get_canonical(self) -> Union['Category', 'Archive']:
        """returns the canonical version of an archive. The main purpose is transforming subsumed archives into their subsumign categories.
        For most archives this returns the archive itself. In the case of archives that are also categories, it return the Archive version of the archive"""
        from .definitions import CATEGORIES
        if self.canonical_id!= self.id and self.canonical_id in CATEGORIES:
            return CATEGORIES[self.canonical_id]
        else:
            return self

class Category(BaseTaxonomy):
    """Represents an arXiv category."""

    in_archive: str
    is_general: bool
    description: Optional[str]

    def get_archive(self) -> Archive:
        """Returns parent archive."""
        from .definitions import ARCHIVES
        return ARCHIVES[self.in_archive]
    
    def get_canonical(self) -> 'Category':
        """returns the canonical version of the category object"""
        from .definitions import CATEGORIES
        if self.canonical_id!= self.id:
            return CATEGORIES[self.canonical_id]
        else:
            return self
        

def create_bad_arch(name: str) -> Archive:
    return Archive(
        id="bad-arch",
        full_name=f"Invalid Archive: {name}",
        is_active=False,
        in_group="grp_bad",
        start_date=date(2024, 1, 1)
    )

def create_bad_category(name:str) -> Category:
    return Category(
        id="bad-arch.bad-cat",
        full_name=f"Invalid Category: {name}",
        is_active=False,
        in_archive="bad-arch",
        is_general=False
    ) 

def get_all_cats_from_string(cat_string:str, only_cannonical:Optional[bool]=False)->Tuple[List[Group], List[Archive],List[Category]]:
    """returns all possble groups, archives and category lists an article would appear in based on the category string.
    This is needed because alternate names are not always recorded in the strings
    setting only_cannonical to true will not return non canonical categories, but will stil return the archives from non-cannonical alias pairs
    This is meant to be used on catgory strings from the database, not user input
    raises KeyError if category string is invalid
    """
    from .definitions import CATEGORIES, CATEGORY_ALIASES
    cats = {CATEGORIES[cat].get_canonical() for cat in cat_string.split()} 
    archives_canon={cat.get_archive() for cat in cats}
    archives_noncanon = {CATEGORIES[cat.alt_name].get_archive() for cat in cats if (cat.alt_name and cat.alt_name in CATEGORY_ALIASES)} #papers also belong in the archives of their non-cannon alias categories
    archives= archives_noncanon | archives_canon
      
    if not only_cannonical:
        noncannon_cats = {CATEGORIES[cat.alt_name] for cat in cats if cat.alt_name is not None and cat.alt_name in CATEGORIES}
        cats= cats | noncannon_cats
        noncannon_archives={cat.get_archive() for cat in noncannon_cats}
        archives= archives | noncannon_archives

    groups={arch.get_group() for arch in archives}
    return list(groups), list(archives), list(cats)