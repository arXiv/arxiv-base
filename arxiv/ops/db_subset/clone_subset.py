from typing import Sequence, List, Type, Dict, Optional
from dataclasses import dataclass, asdict
import json
import os
import importlib
import inspect

from sqlalchemy import (
    create_engine, 
    func, 
    select, 
    Select,
    and_,
    Subquery
)
from sqlalchemy.sql import _typing
from sqlalchemy.orm import sessionmaker, Session

from ...db import Base, LaTeXMLBase, get_db
from ...db.models import (
    Document,
    Submission,
    Metadata,
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

engine = create_engine(os.environ.get('NEW_DB_URI', 'sqlite:///:memory:'))
latexml_engine = create_engine(os.environ.get('NEW_LATEXML_DB_URI', 'sqlite:///:memory:'))

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

def get_tables () -> List[Type]:
    module = importlib.import_module('arxiv.db.models')
    classes = [cls for _, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == 'arxiv.db.models']
    return classes

def get_published_articles (article_count: int) -> Select[Document]:
    return select(Document) \
        .order_by(func.random()) \
        .limit(article_count) \

def get_unpublished_submissions (unpublished_submission_count: int, session: Session) -> Sequence[Submission]:
    return session.execute(
        select(Submission)
        .filter(Submission.doc_paper_id.is_(None))
        .order_by(func.random())
        .limit(unpublished_submission_count)
    ).scalars().all()

@dataclass(frozen=True)
class Edge:
    from_column: str
    to_table: str
    to_column: str
    
def generate_relationship_graph(models: List[Type]):
    adjacency_list = {}

    for model in models:
        table_name = model.__tablename__
        if table_name not in adjacency_list:
            adjacency_list[table_name] = set()

        for column in model.__table__.columns:
            for fk in column.foreign_keys:
                origin_table, origin_column = fk.target_fullname.split('.')

                edge = Edge(origin_column, table_name, column.name)

                if origin_table not in adjacency_list:
                    adjacency_list[origin_table] = set([edge])
                elif edge not in adjacency_list[origin_table]:
                    adjacency_list[origin_table].add(edge)

    for table, edges in adjacency_list.items():
        adjacency_list[table] = list(map(asdict, edges))

    graph_json = json.dumps(adjacency_list)
    return graph_json


def parse_graph_edge (table: Subquery, edge: Dict[str, str], table_map: Dict[str, _typing._TypedColumnClauseArgument]) -> Optional[Select]:
    to_table = table_map[edge['to_table']]
    return (select(to_table)
            .join(table, onclause=(getattr(table.c, edge['from_column']) == getattr(to_table, edge['to_column']))))


def topological_sort(graph):
    visited = set()
    stack = []

    def dfs(node):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)

        # process_node(node)

        stack.append(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return stack[::-1]


def get_subset(article_count: int, unpublished_submission_count: int):
    with get_db() as session:
        articles = get_published_articles(article_count).subquery()
        published = session.execute(
            select(Metadata, Submission, articles)
            .filter(and_(
                Metadata.paper_id == articles.c.paper_id,
                Submission.document_id == Metadata.document_id)
            )
        ).all()

        doc_set = set()
        doc_cols = ['document_id', 'paper_id', 'title', 'authors',
                    'submitter_email', 'submitter_id', 'dated', 
                    'primary_subject_class', 'created', 'submitter']
        metadata = []
        documents = []
        submissions = get_unpublished_submissions(unpublished_submission_count, session)
        for row in published:
            metadata.append(row._t[0])
            submissions.append(row._t[1])
            paper_id = row._t[0].paper_id
            if paper_id not in doc_set:
                documents.append(Document(**dict(zip(doc_cols, row._t[2:]))))
                doc_set.add(paper_id)

        table_map = { t.__tablename__: t for t in get_tables() }
        graph = json.loads(generate_relationship_graph(get_tables()))
        test = session.execute(parse_graph_edge(articles, graph['arXiv_documents'][0], table_map)).all()
        print (test)
        # processed = [Metadata, Document, Submission]
        # table_queue = get_tables()
        # while len(processed) < len(table_queue):
