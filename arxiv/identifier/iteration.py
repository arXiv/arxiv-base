"""Iterator for arxiv IDs."""

from typing import Optional, List

from sqlalchemy import or_

from ..db import get_db
from ..db.models import Metadata
from . import Identifier
from ..taxonomy.category import Category
from ..document.version import SOURCE_FORMAT


class arXivIDIterator:
    """Iterator for arxiv ids."""

    def __init__ (self,
                  start_yymm: str,
                  end_yymm: str,
                  categories: Optional[List[Category]] = None,
                  source_formats: Optional[List[SOURCE_FORMAT]] = None,
                  only_latest_version: bool = False):
        
        with get_db() as session:
            self.query = session.query(Metadata.paper_id, Metadata.version) \
                .filter(Metadata.paper_id >= start_yymm) \
                .filter(Metadata.paper_id < f'{end_yymm}.999999')
            if categories:
                self.query = self.query.filter(or_(*[Metadata.abs_categories.like(f'%{category.id}%') for category in categories]))
            if source_formats:
                self.query = self.query.filter(Metadata.source_format.in_(source_formats))
            if only_latest_version:
                self.query = self.query.filter(Metadata.is_current == 1)
            
            self.ids = self.query.all()

        self.len_ids = len(self.ids)
        self.index = 0

    def __iter__ (self) -> 'arXivIDIterator':
        """Iterator for arXiv ids."""
        return self
    
    def __next__ (self) -> Identifier:
        """Gets next."""
        if self.index >= self.len_ids:
            raise StopIteration
        paper_id, version = self.ids[self.index].tuple()
        self.index += 1
        return Identifier(f'{paper_id}v{version}')
