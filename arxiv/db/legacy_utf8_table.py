"""Consistency checks for columns using the Legacy* (twice cooked utf8) types."""

from typing import Any
from logging import getLogger

from .column_types import LegacyUtf8Mixin, _MYSQL_UTF8_CHARSETS

logger = getLogger(__name__)


def check_legacy_utf8_tables(metadata: Any) -> list[str]:
    """Warn about tables with Legacy* columns whose declared mysql_charset is NOT utf8.

    Applying the double-encoding to a latin1 table would corrupt data. Returns the warnings.
    """
    problems: list[str] = []
    for table in metadata.tables.values():
        cols = [c.name for c in table.columns if isinstance(c.type, LegacyUtf8Mixin)]
        if not cols:
            continue
        charset = table.kwargs.get("mysql_charset")  # None when the table declares none
        if charset not in _MYSQL_UTF8_CHARSETS:
            msg = (f"Table {table.name} has legacy-utf8 columns {cols} but declared "
                   f"mysql_charset is {charset!r}, expected utf8/utf8mb3")
            logger.warning(msg)
            problems.append(msg)
    return problems


def check_legacy_utf8_table_columns_in_db(metadata: Any, engine: Any) -> list[str]:
    """Warn when the real DB column charset of Legacy* columns is not utf8.

    Reads information_schema, so it needs a live MySQL connection.
    """
    from sqlalchemy import text
    problems: list[str] = []
    wanted: dict[str, list[str]] = {
        t.name: [c.name for c in t.columns if isinstance(c.type, LegacyUtf8Mixin)]
        for t in metadata.tables.values()
    }
    wanted = {t: cols for t, cols in wanted.items() if cols}
    if not wanted:
        return problems
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE()"
        )).all()
    actual = {(r[0], r[1]): r[2] for r in rows}
    for table, cols in wanted.items():
        for col in cols:
            charset = actual.get((table, col))
            if charset not in _MYSQL_UTF8_CHARSETS:
                msg = f"Column {table}.{col} is {charset!r} in the database, expected utf8/utf8mb3"
                logger.warning(msg)
                problems.append(msg)
    return problems
