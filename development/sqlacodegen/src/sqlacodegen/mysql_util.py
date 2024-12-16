from sqlalchemy.engine import Connection, Engine
from sqlalchemy import text

def get_mysql_table_charsets(engine: Engine, schema_name: str) -> dict:
    # Query to fetch table names and their character sets
    query = f"""
        SELECT 
            TABLE_NAME,
            SUBSTRING_INDEX(TABLE_COLLATION, '_', 1) AS CHARACTER_SET
        FROM 
            INFORMATION_SCHEMA.TABLES
        WHERE 
            TABLE_SCHEMA = '{schema_name}';
    """

    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        charsets = {row[0]: row[1] for row in result}


    return charsets
