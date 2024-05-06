from typing import Sequence, List, Type, Dict, Optional, Literal, Any
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
    Subquery,
    insert
)
from sqlalchemy.sql import _typing
from sqlalchemy.orm import sessionmaker, Session

from ...db import Base, LaTeXMLBase, SessionLocal
from ...db import engine as classic_engine
from ...db.models import (
    TapirUsersPassword,
    OrcidIds,
    Document,
    Submission,
    DBLaTeXMLDocuments,
    DBLaTeXMLSubmissions,
    DBLaTeXMLFeedback,
    TapirUser,
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

new_engine = create_engine(os.environ.get('NEW_DB_URI', 'sqlite:///temp.db'))

NewSessionLocal = sessionmaker(autocommit=False, autoflush=True)
NewSessionLocal.configure(bind=new_engine)

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
            .join(table, onclause=(getattr(table.c, edge.from_column) == getattr(to_table, edge.to_column))))


def topological_sort(graph: Dict[str, List[str]]):
    visited = set()
    stack = []

    def dfs(node: str):
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


# def get_subset(article_count: int, unpublished_submission_count: int):
#     with get_db() as session:
#         articles = get_published_articles(article_count).subquery()
#         published = session.execute(
#             select(Metadata, Submission, articles)
#             .filter(and_(
#                 Metadata.paper_id == articles.c.paper_id,
#                 Submission.document_id == Metadata.document_id)
#             )
#         ).all()

#         doc_set = set()
#         doc_cols = ['document_id', 'paper_id', 'title', 'authors',
#                     'submitter_email', 'submitter_id', 'dated', 
#                     'primary_subject_class', 'created', 'submitter']
#         metadata = []
#         documents = []
#         submissions = get_unpublished_submissions(unpublished_submission_count, session)
#         for row in published:
#             metadata.append(row._t[0])
#             submissions.append(row._t[1])
#             paper_id = row._t[0].paper_id
#             if paper_id not in doc_set:
#                 documents.append(Document(**dict(zip(doc_cols, row._t[2:]))))
#                 doc_set.add(paper_id)

#         table_map = { t.__tablename__: t for t in get_tables() }
#         graph = json.loads(generate_relationship_graph(get_tables()))
#         test = session.execute(parse_graph_edge(articles, graph['arXiv_documents'][0], table_map)).all()
#         print (test)
#         # processed = [Metadata, Document, Submission]
#         # table_queue = get_tables()
#         # while len(processed) < len(table_queue):

SpecialCase = Literal['all', 'none']

def _copy_all_rows (table: Type, classic_session: Session, new_session: Session):
    # table.create(new_session) # 
    rows = classic_session.execute(select(table)).scalars().all()
    new_session.add_all(rows)
    new_session.commit()

def _process_node (table: Any, edges: List[Edge], table_map: Dict[str, Any], query_map: Dict[str, Subquery], special_cases: Dict[str, str]) -> Subquery:
    if table == OrcidIds:
        breakpoint()
    stmt = select(*[getattr(table.__table__.c, col.key) for col in table.__table__.columns])
    uniq_parents = set(map(lambda x: x.to_table, edges))
    parent_edges = { x: list(filter(lambda y: y.to_table == x, edges)) for x in uniq_parents }
    for parent, edge_list in parent_edges.items():
        if special_cases.get(parent) == 'all':
            continue
        if len(edge_list) > 1:
            subq = query_map[parent]
            on = getattr(table, edge_list[0].from_column) == getattr(subq.c, edge_list[0].to_column)
            for edge in edge_list[1:]:
                on = on & (getattr(table, edge.from_column) == getattr(subq.c, edge.to_column))
            stmt = stmt.join(subq, onclause=on)
        else:
            edge = edge_list[0]
            subq = query_map[edge.to_table]
            stmt = stmt.join(subq, onclause=(getattr(table, edge.from_column) == getattr(subq.c, edge.to_column)))
    """
    SELECT * FROM arXiv_orcid_ids JOIN (SELECT * FROM tapir_users WHERE ...) as anon_1 ON anon_1.user_id == arXiv_orcid_ids.user_id;
    """
    return stmt.subquery()

def _generate_seed_table (classic_session: Session) -> Subquery:
    SIZE = 10
    ids = classic_session.scalars(select(TapirUser.user_id).order_by(func.random()).limit(SIZE)).all()
    return select(TapirUser).filter(TapirUser.user_id.in_(ids)).subquery()


def _write_subquery (table: Any, subq: Subquery, classic_session: Session, new_session: Session):
    if table == OrcidIds:
        breakpoint()
        print (select(subq).compile(new_engine, compile_kwargs={"literal_binds": True}))
        print (f'TAPIR USERS COUNT: {len(new_session.execute(select(TapirUser)).all())}')
    stmt = select(subq)
    rows = map(lambda x: table(**dict(zip(table.__table__.columns.keys(), x._t))), classic_session.execute(stmt, bind_arguments={'bind': classic_engine}).all())
    for i, row in enumerate(rows):
        print (f'{row}: {row.__dict__}')
        values = row.__dict__
        del values['_sa_instance_state']
        new_session.execute(insert(row.__table__).values(**values))
        new_session.commit()
    

def _invert_db_graph_edges (db_graph: Dict[str, List[Edge]]) -> Dict[str, List[Edge]]:
    inverted_db_graph = { i: [] for i in db_graph }
    for node in db_graph:
        for next in db_graph[node]:
            reversed_edge = Edge(
                    from_column=next.to_column,
                    to_table=node,
                    to_column=next.from_column
                )
            if next.to_table in inverted_db_graph:
                inverted_db_graph[next.to_table].append(reversed_edge)
            else:
                inverted_db_graph[next.to_table] = [reversed_edge]
    return inverted_db_graph

def make_subset (db_graph: Dict[str, List[Edge]], 
                 special_cases: Dict[str, SpecialCase], 
                 **kwargs):
    """
    algorithm:

    1. make topological sort of nodes
    2. work through nodes, looking up what action to take for each
    in special cases config, otherwise defaulting to join on 
    FK's (a.k.a parse_graph_edge)
    """

    ### Set up ###
    # latexml_tables = set([DBLaTeXMLDocuments, DBLaTeXMLSubmissions, DBLaTeXMLFeedback])
    classic_session = SessionLocal()
    new_session = NewSessionLocal()

    Base.metadata.drop_all(new_engine)
    Base.metadata.create_all(new_engine)
    LaTeXMLBase.metadata.drop_all(new_engine)
    LaTeXMLBase.metadata.create_all(new_engine)
    
    ### Do algorithm ###
    table_lookup = { i.__tablename__: i for i in get_tables() }
    processing_order = topological_sort({ k: list(map(lambda x: x.to_table, v)) for k,v in db_graph.items() })
    inverted_db_graph = _invert_db_graph_edges(db_graph)
    table_queries: Dict[str, Subquery] = {}
    TapirUser.__table__.columns.keys

    for table_name in processing_order:
        table = table_lookup[table_name]
        if table_name in special_cases:
            special_case = special_cases[table_name]
            if special_case == 'all':
                # _copy_all_rows(table, classic_session, new_session)
                continue
            elif special_case == 'seed':
                table_queries[table_name] = _generate_seed_table (classic_session)
                breakpoint()
                print (select(table_queries[table_name]).compile(new_engine, compile_kwargs={"literal_binds": True}))
            else: # special case is 'none'
                # table.__table__.create(new_session)
                # new_session.commit()
                continue
        else:
            table_queries[table_name] = _process_node (table, 
                                                       inverted_db_graph[table_name], 
                                                       table_lookup,
                                                       table_queries,
                                                       special_cases)
        
    for table in processing_order:
        print (f"WRITING TABLE {table}")
        subq = table_queries.get(table)
        if subq is not None:
            # print (select(subq).compile(engine, compile_kwargs={"literal_binds": True}))
            _write_subquery(table_lookup[table], subq, classic_session, new_session)
        else:
            print ("NO SUBQUERY AVAILABLE")

    print (processing_order)

    ### Clean up ###
    classic_session.close()
    new_session.commit()

    print ('PRINTING TAPIR_USERS')
    for i in new_session.execute(select(TapirUser)).scalars().all():
        print (i)

    new_session.close()

def do_temp ():
    graph = json.loads(open('arxiv/ops/db_subset/config/graph_no_latexml.json').read())
    db_graph = { k: list(map(lambda x: Edge(**x), v)) for k,v in graph.items() }
    special_cases = json.loads(open('arxiv/ops/db_subset/config/special_cases.json').read())
    make_subset(db_graph, special_cases)