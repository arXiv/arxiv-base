from typing import Tuple
from contextlib import contextmanager
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ...db import Base, LaTeXMLBase, get_db
from ...db.models import (
    t_arXiv_stats_hourly,
    t_arXiv_admin_state,
    t_arXiv_bad_pw,
    t_arXiv_black_email,
    t_arXiv_block_email,
    t_arXiv_bogus_subject_class,
    t_arXiv_duplicates,
    t_arXiv_in_category,
    t_arXiv_moderators,
    t_arXiv_ownership_requests_papers,
    t_arXiv_refresh_list,
    t_arXiv_paper_owners,
    t_arXiv_updates_tmp,
    t_arXiv_white_email,
    t_arXiv_xml_notifications,
    t_demographics_backup,
    t_tapir_email_change_tokens_used,
    t_tapir_email_tokens_used,
    t_tapir_error_log,
    t_tapir_no_cookies,
    t_tapir_periodic_tasks_log,
    t_tapir_periodic_tasks_log,
    t_tapir_permanent_tokens_used,
    t_tapir_save_post_variables
)

@contextmanager
def get_new_db (DB_URI: str):
    engine = create_engine(os.environ['NEW_DB_URI'])
    latexml_engine = create_engine(os.environ['NEW_LATEXML_DB_URI'])

    SessionLocal = sessionmaker(autcommit=False, autoflush=True)

    SessionLocal.configure(binds={
        Base: engine,
        LaTeXMLBase: latexml_engine,
        t_arXiv_stats_hourly: engine,
        t_arXiv_admin_state: engine,
        t_arXiv_bad_pw: engine,
        t_arXiv_black_email: engine,
        t_arXiv_block_email: engine,
        t_arXiv_bogus_subject_class: engine,
        t_arXiv_duplicates: engine,
        t_arXiv_in_category: engine,
        t_arXiv_moderators: engine,
        t_arXiv_ownership_requests_papers: engine,
        t_arXiv_refresh_list: engine,
        t_arXiv_paper_owners: engine,
        t_arXiv_updates_tmp: engine,
        t_arXiv_white_email: engine,
        t_arXiv_xml_notifications: engine,
        t_demographics_backup: engine,
        t_tapir_email_change_tokens_used: engine,
        t_tapir_email_tokens_used: engine,
        t_tapir_error_log: engine,
        t_tapir_no_cookies: engine,
        t_tapir_periodic_tasks_log: engine,
        t_tapir_periodic_tasks_log: engine,
        t_tapir_permanent_tokens_used: engine,
        t_tapir_save_post_variables: engine
    })

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_subset (article_count: int):
    ...
    