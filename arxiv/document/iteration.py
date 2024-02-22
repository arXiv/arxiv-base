from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    text,
    TIMESTAMP,
    or_
)

from ..identifier import Identifier
from ..taxonomy.category import Category
from ..document.version import SOURCE_FORMAT

db: SQLAlchemy = SQLAlchemy()


class Metadata(db.Model):
    """Model for arXiv document metadata."""

    __tablename__ = "arXiv_metadata"
    __table_args__ = (Index("pidv", "paper_id", "version", unique=True),)

    metadata_id = Column(Integer, primary_key=True)
    document_id = Column(
        ForeignKey(
            "arXiv_documents.document_id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
        server_default=text("'0'"),
    )
    paper_id = Column(String(64), nullable=False)
    created = Column(DateTime)
    updated = Column(DateTime)
    submitter_id = Column(ForeignKey("tapir_users.user_id"), index=True)
    submitter_name = Column(String(64), nullable=False)
    submitter_email = Column(String(64), nullable=False)
    source_size = Column(Integer)
    source_format = Column(String(12))
    source_flags = Column(String(12))
    title = Column(Text)
    authors = Column(Text)
    abs_categories = Column(String(255))
    comments = Column(Text)
    proxy = Column(String(255))
    report_num = Column(Text)
    msc_class = Column(String(255))
    acm_class = Column(String(255))
    journal_ref = Column(Text)
    doi = Column(String(255))
    abstract = Column(Text)
    license = Column(ForeignKey("arXiv_licenses.name"), index=True)
    version = Column(Integer, nullable=False, server_default=text("'1'"))
    modtime = Column(Integer)
    is_current = Column(Integer, server_default=text("'1'"))
    is_withdrawn = Column(Integer, nullable=False, server_default=text("'0'"))

    # document = relationship("Document")
    # arXiv_license = relationship("License")
    # submitter = relationship("User")

@dataclass
class arXivDocumentFilter:
    start_date: datetime = datetime.min
    end_date: datetime = datetime.max
    yymm: Optional[str] = None
    categories: Optional[List[Category]] = None
    source_formats: Optional[List[SOURCE_FORMAT]] = None

    def validate (self) -> bool:
        return
    
##########################################################################################
##########################################################################################
##########################################################################################

class arXivIDIterator:

    def __init__ (self,
                  start_yymm: str,
                  end_yymm: str,
                  categories: Optional[List[Category]] = None,
                  source_formats: Optional[List[SOURCE_FORMAT]] = None,
                  only_latest_version: bool = False):
        
        self.query = db.session.query(Metadata.paper_id, Metadata.version) \
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
        return self
    
    def __next__ (self) -> Identifier:
        if self.index >= self.len_ids:
            raise StopIteration
        paper_id, version = self.ids[self.index].tuple()
        self.index += 1
        return Identifier(f'{paper_id}v{version}')