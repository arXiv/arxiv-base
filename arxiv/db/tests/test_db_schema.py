import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Without this import, Base.metadata does not get populated. So it may look doing nothing but do not remove this.
import arxiv.db.models

from .. import Base, LaTeXMLBase, session_factory, _classic_engine as classic_engine

def test_db_schema():
    db_engine = create_engine(os.environ['TEST_ARXIV_DB_URI'])

    SessionLocal = sessionmaker(autocommit=False, autoflush=True)
    SessionLocal.configure(bind=db_engine)
    db_session = SessionLocal(autocommit=False, autoflush=True)
    db_session.execute(text('select 1'))

    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    LaTeXMLBase.metadata.drop_all(db_engine)
    LaTeXMLBase.metadata.create_all(db_engine)

    db_session.commit()
