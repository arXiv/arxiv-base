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
    Subquery,
    insert
)
from sqlalchemy.sql import tuple_
from sqlalchemy.orm import (
    sessionmaker, 
    Session,
    make_transient
)

from ...db import Base, LaTeXMLBase, session_factory
from ...db import engine as classic_engine
from ...db.models import (
    DBLaTeXMLDocuments,
    DBLaTeXMLSubmissions,
    TapirUser,
)

new_engine = create_engine(os.environ.get('NEW_DB_URI', 'sqlite:///temp.db'))

NewSessionLocal = sessionmaker(autocommit=False, autoflush=True)
NewSessionLocal.configure(bind=new_engine)

def get_tables () -> List[Type]:
    module = importlib.import_module('arxiv.db.models')
    classes = [cls for _, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == 'arxiv.db.models']
    return classes


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


def topological_sort(graph: Dict[str, List[str]]):
    visited = set()
    stack = []

    def dfs(node: str):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)
        stack.append(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return stack[::-1]


SpecialCase = Literal['all', 'none']

def _copy_all_rows (table: Type, classic_session: Session, new_session: Session):
    rows = classic_session.execute(select(table)).scalars().all()
    for i, row in enumerate(rows):
        values = row.__dict__
        del values['_sa_instance_state']
        new_session.execute(insert(row.__table__).values(**values))
        if i % 1000 == 0:
            print (f'Writing {table.__tablename__}, on row #{i}')
            new_session.commit()
    new_session.commit()

def _process_node (table: Any, edges: List[Edge], query_map: Dict[str, Subquery], special_cases: Dict[str, str]) -> Subquery:
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
    return stmt.subquery()

def _generate_seed_table (n_users: int, classic_session: Session) -> Subquery:
    ids = classic_session.scalars(select(TapirUser.user_id).order_by(func.random()).limit(n_users)).all()
    return select(TapirUser).filter(TapirUser.user_id.in_(ids)).subquery()

def _write_subquery (table: Any, subq: Subquery, classic_session: Session, new_session: Session):
    stmt = select(subq)
    column_keys: List = table.__table__.columns.keys()
    if 'class' in column_keys:
        column_keys[column_keys.index('class')] = '_class'
    rows = map(lambda x: table(**dict(zip(column_keys, x._t))), classic_session.execute(stmt, bind_arguments={'bind': classic_engine}).all())
    for i, row in enumerate(rows):
        values = row.__dict__
        del values['_sa_instance_state']
        if '_class' in values:
            values['class'] = values['_class']
            del values['_class']
        new_session.execute(insert(row.__table__).values(**values))
        if i % 1000 == 0:
            print (f'Writing {table.__tablename__}, on row #{i}')
            new_session.commit()
    new_session.commit()

def _insert_latexml_tables (query_map: Dict[str, Subquery], classic_session: Session, new_session: Session):
    documents = classic_session.execute(select(query_map['arXiv_metadata'])).all()
    ids = [(x[2], x[-4]) for x in documents]
    for i in range(0, len(ids), 500):
        latexml_docs = classic_session.execute(
            select(DBLaTeXMLDocuments)
            .filter(tuple_(DBLaTeXMLDocuments.paper_id, DBLaTeXMLDocuments.document_version).in_(ids[i: min(len(ids), i+500)]))
        ).scalars().all()
        for row in latexml_docs:
            make_transient(row)
            new_session.add(row)
        new_session.commit()

    submissions = classic_session.execute(select(query_map['arXiv_submissions'])).all()
    sub_ids = [x[0] for x in submissions]
    for i in range(0, len(sub_ids), 500):
        latexml_subs = classic_session.execute(
            select(DBLaTeXMLSubmissions)
            .filter(DBLaTeXMLSubmissions.submission_id.in_(sub_ids[i: min(len(sub_ids), i+500)]))
        ).scalars().all()
        for row in latexml_subs:
            make_transient(row)
            new_session.add(row)
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

def _make_subset (db_graph: Dict[str, List[Edge]], 
                 special_cases: Dict[str, SpecialCase], 
                 size: int):
    """
    algorithm:

    1. make topological sort of nodes
    2. work through nodes, looking up what action to take for each
    in special cases config, otherwise defaulting to join on 
    FK's
    """

    ### Set up ###
    classic_session = session_factory()
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
                print (f'COPYING ENTIRE TABLE {table_name}')
                _copy_all_rows(table, classic_session, new_session)
                continue
            elif special_case == 'seed':
                table_queries[table_name] = _generate_seed_table (size, classic_session)
            else: # special case is 'none'
                continue
        else:
            table_queries[table_name] = _process_node (table, 
                                                       inverted_db_graph[table_name], 
                                                       table_queries,
                                                       special_cases)
        
    for table in processing_order:
        print (f"WRITING TABLE {table}")
        subq = table_queries.get(table)
        if subq is not None:
            _write_subquery(table_lookup[table], subq, classic_session, new_session)
        else:
            print ("NO SUBQUERY AVAILABLE")

    _insert_latexml_tables (table_queries, classic_session, new_session)

    ### Clean up ###
    classic_session.close()

    new_session.commit()
    new_session.close()

def clone_db_subset (n_users: int, config_directory: str):
    graph = json.loads(open(os.path.join(config_directory, 'graph.json')).read())
    special_cases = json.loads(open(os.path.join(config_directory, 'special_cases.json')).read())
    graph_with_edges = { k: list(map(lambda x: Edge(**x), v)) for k,v in graph.items() }
    _make_subset(graph_with_edges, special_cases, n_users)