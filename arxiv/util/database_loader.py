"""
database_loader.py
  Loading database utility
"""

import logging
from ruamel.yaml import YAML
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from arxiv.util.dict_io import from_file_to_dict

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Read json/yaml file and load to database.

    The top-level key is the table name, and the
    """

    engine: Engine

    def __init__(self, engine: Engine):
        self.engine = engine

    def load_data(self, data: dict) -> None:
        with Session(self.engine) as session:
            for table_name, rows in data.items():
                for row in rows:
                    col_names = ", ".join(row.keys())  # Extract column names
                    col_placeholders = ", ".join(
                        [f":{col}" for col in row.keys()]
                    )  # Create placeholders
                    sql_statement = f"INSERT INTO {table_name} ({col_names}) VALUES ({col_placeholders})"
                    try:
                        session.execute(text(sql_statement), row)
                    except Exception as exc:
                        logger.error(f"Statement {sql_statement} data: {row!r}")
                        raise
            session.commit()

    def load_data_from_files(self, filenames: [str]) -> None:
        for filename in filenames:
            self.load_data(from_file_to_dict(filename))
