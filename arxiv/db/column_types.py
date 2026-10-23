"""Custom SQLAlchemy types for handling mixed latin1/utf8 encoding in legacy databases.

These TypeDecorators handle transcoding from bytes to strings based on the column's character set.
"""

from typing import Optional, Any, Type
from sqlalchemy import TypeDecorator, String, Text, LargeBinary, func, event
from sqlalchemy.orm import Mapper
from sqlalchemy.sql.type_api import TypeEngine, _CT
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.dialects import mysql
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql.elements import ColumnElement
from logging import getLogger

logger = getLogger(__name__)


class BinaryStringComparator(UserDefinedType.Comparator):
    """Custom comparator for binary string operations.

    Ensures string operations like contains(), startswith() work correctly
    by encoding the comparison value as bytes and using binary comparison.
    """

    def __clause_element__(self) -> ColumnElement[_CT]:
        """Return the column without BINARY cast for comparisons."""
        return self.expr

    def _binary_compare(self, other: Any, operator: Any) -> Any:
        """Helper to encode the comparison value and use binary comparison."""
        if isinstance(other, str):
            # Encode the string to bytes using UTF-8
            other = other.encode('utf-8')
        # Compare using BINARY cast on both sides
        return operator(func.cast(self.expr, LargeBinary), func.cast(other, LargeBinary))

    def contains(self, other: Any, **kwargs: Any) -> Any:
        """Override contains to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        # Use LIKE with BINARY
        pattern = b'%' + other + b'%'
        return func.cast(self.expr, LargeBinary).like(func.cast(pattern, LargeBinary))

    def startswith(self, other: Any, escape: Optional[str] = None, autoescape: bool = False) -> Any:
        """Override startswith to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        pattern = other + b'%'
        return func.cast(self.expr, LargeBinary).like(func.cast(pattern, LargeBinary))

    def endswith(self, other: Any, escape: Optional[str] = None, autoescape: bool = False) -> Any:
        """Override endswith to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        pattern = b'%' + other
        return func.cast(self.expr, LargeBinary).like(func.cast(pattern, LargeBinary))


class BinaryStringType(TypeDecorator):
    """String type that handles mixed latin1/utf8 encoding for VARCHAR columns.

    Usage:
        class MyModel(Base):
            # For utf8 columns
            name: Mapped[str] = mapped_column(BinaryStringType(255, charset='utf-8'))

            # For latin1 columns
            legacy_field: Mapped[str] = mapped_column(BinaryStringType(255, charset='latin1'))

    """

    impl = String
    cache_ok = False  # column_expression/bind_expression modify SQL generation

    comparator_factory: Type[BinaryStringComparator] = BinaryStringComparator

    def __init__(self, length: Optional[int] = None,
                 charset: Optional[str] = None,
                 fallback_charset: str = 'utf-8',
                 **kwargs: Any) -> None:
        """
        Args:
            length: Maximum string length (for VARCHAR)
            charset: Expected character set ('utf8mb3', 'utf8mb4', 'latin1', etc.)
                    If None, will auto-detect
            fallback_charset: Charset to use if primary decoding fails (default: latin1)
            **kwargs: Additional arguments passed to String type
        """
        super().__init__(length=length, **kwargs)
        self.charset = charset
        self.fallback_charset = fallback_charset

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Use MySQL-specific VARCHAR type."""
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.VARCHAR(length=self.length))
        return dialect.type_descriptor(String(length=self.length))

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """Convert bytes from database to string.

        When use_unicode=False, MySQL connector returns bytes.
        This method handles transcoding based on the configured charset.
        """
        if value is None:
            return None

        # Already a string (shouldn't happen with use_unicode=False, but handle it)
        if isinstance(value, str):
            return value

        # Not bytes, return as-is
        if not isinstance(value, bytes):
            return str(value)

        # Transcode bytes to string
        if self.charset:
            # Use specified charset
            try:
                return value.decode(self.charset)
            except UnicodeDecodeError as e:
                logger.warning(f"Failed to decode with {self.charset}, trying {self.fallback_charset}: {e}")
                return value.decode(self.fallback_charset, errors='replace')
        else:
            # Auto-detect: try utf8 first, fallback to latin1
            try:
                return value.decode('utf8')
            except UnicodeDecodeError:
                return value.decode(self.fallback_charset, errors='replace')

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[bytes]:
        """Handle encoding for INSERT/UPDATE.

        When use_unicode=False, we encode strings to bytes using the target charset.
        This ensures the MySQL connector sends the correct byte representation.

        Returns:
            bytes: Encoded value in the target charset
        """
        if value is None:
            return None

        # If already bytes, assume it's in the correct encoding
        if isinstance(value, bytes):
            return value

        # Convert to string first if needed
        str_value: str = value if isinstance(value, str) else str(value)

        # Encode to bytes using the target charset
        target_charset = self.charset or 'utf8'
        try:
            return str_value.encode(target_charset)
        except UnicodeEncodeError as e:
            logger.warning(f"Failed to encode with {target_charset}, using utf8 with replace: {e}")
            return str_value.encode('utf8', errors='replace')

    def bind_expression(self, bindvalue: Any) -> Any:
        """Wrap bind parameters with MySQL's BINARY() function.

        This makes SQLAlchemy generate SQL like:
            UPDATE table SET column=binary(%s)
        instead of:
            UPDATE table SET column=%s

        The BINARY() cast bypasses MySQL's character set validation,
        allowing UTF-8 bytes to be stored in latin-1 columns.
        """
        return func.cast(bindvalue, LargeBinary)

    def column_expression(self, col: Any) -> Any:
        """Wrap column in BINARY cast for SELECT queries.

        This makes SQLAlchemy generate SQL like:
            SELECT CAST(column AS BINARY) FROM table
        instead of:
            SELECT column FROM table

        This ensures MySQL returns the raw bytes without latin-1 interpretation,
        so we can decode them as UTF-8 in process_result_value.
        """
        from sqlalchemy import type_coerce
        return type_coerce(func.cast(col, LargeBinary), self)


class TranscodedText(TypeDecorator):
    """Text type that handles mixed latin1/utf8 encoding for TEXT columns.

    Similar to TranscodedString but for TEXT/MEDIUMTEXT/LONGTEXT columns.

    Usage:
        class MyModel(Base):
            description: Mapped[str] = mapped_column(TranscodedText(charset='utf8mb3'))
            legacy_notes: Mapped[str] = mapped_column(TranscodedText(charset='latin1'))
    """

    impl = Text
    cache_ok = False  # column_expression/bind_expression modify SQL generation

    comparator_factory: Type[BinaryStringComparator] = BinaryStringComparator

    def __init__(self, charset: Optional[str] = None,
                 fallback_charset: str = 'latin1',
                 **kwargs: Any) -> None:
        """
        Args:
            charset: Expected character set ('utf8mb3', 'utf8mb4', 'latin1', etc.)
                    If None, will auto-detect
            fallback_charset: Charset to use if primary decoding fails (default: latin1)
            **kwargs: Additional arguments passed to Text type
        """
        super().__init__(**kwargs)
        self.charset = charset
        self.fallback_charset = fallback_charset

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Use MySQL-specific TEXT type."""
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.TEXT())
        return dialect.type_descriptor(Text())

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """Convert bytes from database to string."""
        if value is None:
            return None

        if isinstance(value, str):
            return value

        if not isinstance(value, bytes):
            return str(value)

        # Transcode bytes to string
        if self.charset:
            try:
                return value.decode(self.charset)
            except UnicodeDecodeError as e:
                logger.warning(f"Failed to decode with {self.charset}, trying {self.fallback_charset}: {e}")
                return value.decode(self.fallback_charset, errors='replace')
        else:
            # Auto-detect: try utf8 first, fallback to latin1
            try:
                return value.decode('utf8')
            except UnicodeDecodeError:
                return value.decode(self.fallback_charset, errors='replace')

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[bytes]:
        """Handle encoding for INSERT/UPDATE.

        When use_unicode=False, we encode strings to bytes using the target charset.
        This ensures the MySQL connector sends the correct byte representation.

        Returns:
            bytes: Encoded value in the target charset
        """
        if value is None:
            return None

        # If already bytes, assume it's in the correct encoding
        if isinstance(value, bytes):
            return value

        # Convert to string first if needed
        str_value: str = value if isinstance(value, str) else str(value)

        # Encode to bytes using the target charset
        target_charset = self.charset or 'utf8'
        try:
            return str_value.encode(target_charset)
        except UnicodeEncodeError as e:
            logger.warning(f"Failed to encode with {target_charset}, using utf8 with replace: {e}")
            return str_value.encode('utf8', errors='replace')

    def bind_expression(self, bindvalue: Any) -> Any:
        """Wrap bind parameters with MySQL's BINARY() function.

        This makes SQLAlchemy generate SQL like:
            UPDATE table SET column=binary(%s)
        instead of:
            UPDATE table SET column=%s

        The BINARY() cast bypasses MySQL's character set validation,
        allowing UTF-8 bytes to be stored in latin-1 columns.
        """
        return func.cast(bindvalue, LargeBinary)

    def column_expression(self, col: Any) -> Any:
        """Wrap column in BINARY cast for SELECT queries.

        This makes SQLAlchemy generate SQL like:
            SELECT CAST(column AS BINARY) FROM table
        instead of:
            SELECT column FROM table

        This ensures MySQL returns the raw bytes without latin-1 interpretation,
        so we can decode them as UTF-8 in process_result_value.
        """
        from sqlalchemy import type_coerce
        return type_coerce(func.cast(col, LargeBinary), self)


# Convenience type for common cases

class Utf8String(BinaryStringType):
    """VARCHAR column with utf8mb3 encoding."""
    cache_ok = False

    def __init__(self, length: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(length=length, charset='utf-8', **kwargs)

    @classmethod
    def column_factory(cls, length: Optional[int] = None, **kwargs: Any) -> "Utf8String":
        """Return Utf8String for MySQL with a plain String fallback for SQLite."""
        return cls(length=length, **kwargs).with_variant(String(length=length), "sqlite")


class Utf8Text(TranscodedText):
    """TEXT column with utf8mb3 encoding."""
    cache_ok = False

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(charset='utf-8', **kwargs)

    @classmethod
    def column_factory(cls, **kwargs: Any) -> "Utf8Text":
        """Return Utf8Text for MySQL with a plain Text fallback for SQLite."""
        return cls(**kwargs).with_variant(Text, "sqlite")

# Columns in utf8 tables that the legacy app wrote through a latin1 connection.
#
# The legacy connection treats its utf8 bytes as latin1 and the server re-encodes them to utf8,
# so the stored text is double-encoded ("é" is stored as "Ã©"). The legacy connection reverses
# this on read. Our connection is utf8mb4, so we reverse and reapply it here. No BINARY casts:
# the server must see ordinary character data so that comparisons and LIKE work on the
# double-encoded form (bind parameters pass through process_bind_param too).
#
# A legacy (latin1) reader gets "?" for any stored character outside latin1, so a value written
# single-encoded by some other writer is lossy for every legacy reader. Writing through these
# types always stores the double-encoded form.

_MYSQL_UTF8_CHARSETS = ("utf8", "utf8mb3")

# MySQL's latin1 is cp1252, except that the five bytes cp1252 leaves undefined
# (0x81/0x8d/0x8f/0x90/0x9d) map to the C1 controls U+0081 etc. Byte -> char, and back.
_LATIN1_CHAR = tuple(bytes([b]).decode("cp1252", errors="ignore") or chr(b) for b in range(256))
_LATIN1_BYTE = {c: b for b, c in enumerate(_LATIN1_CHAR)}


def legacy_utf8_decode(value: str) -> str:
    """Undo the legacy double encoding, one UTF-8 sequence at a time.

    Each run of characters whose latin1 bytes form one valid UTF-8 sequence is replaced by the
    character it encodes; everything else is kept as stored. So a fully double-encoded value
    decodes completely, a single-encoded value ("Müller", "Cătălina") comes back unchanged, and a
    value that mixes both (e.g. double-encoded text plus a stray U+FFFD) decodes where it can.
    Re-encoding the result with legacy_utf8_encode() then yields a fully double-encoded value, so
    an edit never adds a second layer to the part that was already double-encoded.
    """
    if value.isascii():
        return value
    out = []
    i, n = 0, len(value)
    while i < n:
        lead = _LATIN1_BYTE.get(value[i])
        if lead is not None and 0xC2 <= lead <= 0xF4:
            size = 2 if lead < 0xE0 else 3 if lead < 0xF0 else 4
            seq = [_LATIN1_BYTE.get(c) for c in value[i:i + size]]
            if len(seq) == size and None not in seq:
                try:
                    out.append(bytes(seq).decode("utf-8"))  # validates continuation bytes too
                    i += size
                    continue
                except UnicodeDecodeError:
                    pass
        out.append(value[i])
        i += 1
    return "".join(out)


def legacy_utf8_encode(value: str) -> str:
    """Apply the legacy double encoding: each UTF-8 byte of value becomes one latin1 character."""
    if value.isascii():
        return value
    return "".join(_LATIN1_CHAR[b] for b in value.encode("utf-8"))


class LegacyUtf8TooLong(ValueError):
    """A value is longer than its column once double-encoded (VARCHAR counts encoded characters)."""

    def __init__(self, column: str, length: int, encoded_length: int) -> None:
        super().__init__(f"{column}: {encoded_length} characters once stored double-encoded, "
                         f"the column holds {length}")
        self.column = column
        self.length = length
        self.encoded_length = encoded_length


class LegacyUtf8Mixin:
    """Undo/redo the legacy double encoding. Mix into a TypeDecorator."""

    cache_ok = True

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return legacy_utf8_decode(value)

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return legacy_utf8_encode(value)


class LegacyUtf8String(LegacyUtf8Mixin, TypeDecorator):
    """VARCHAR in a utf8 table written by the legacy latin1 connection."""
    impl = String
    cache_ok = True

    @classmethod
    def column_factory(cls, length: Optional[int] = None, **kwargs: Any) -> "LegacyUtf8String":
        """Return LegacyUtf8String for MySQL with a plain String fallback for SQLite."""
        return cls(length=length, **kwargs).with_variant(String(length=length), "sqlite")


class LegacyUtf8Text(LegacyUtf8Mixin, TypeDecorator):
    """TEXT in a utf8 table written by the legacy latin1 connection."""
    impl = Text
    cache_ok = True

    @classmethod
    def column_factory(cls, **kwargs: Any) -> "LegacyUtf8Text":
        """Return LegacyUtf8Text for MySQL with a plain Text fallback for SQLite."""
        return cls(**kwargs).with_variant(Text, "sqlite")


# The length check runs when a mapped attribute is assigned, not in process_bind_param: a bind
# parameter can also be a WHERE or LIKE operand, which may legitimately be longer than the column.
# Without it, strict MySQL rejects the row (1406) and non-strict MySQL cuts the value in the middle
# of an encoded sequence, which then reads back as mojibake for good.

def _length_checker(column: str, length: int) -> Any:
    def check(target: Any, value: Any, oldvalue: Any, initiator: Any) -> None:
        if isinstance(value, str) and not value.isascii():
            encoded = len(legacy_utf8_encode(value))
            if encoded > length:
                raise LegacyUtf8TooLong(column, length, encoded)
    return check


@event.listens_for(Mapper, "mapper_configured")
def _add_legacy_utf8_length_checks(mapper: Mapper, class_: Any) -> None:
    for prop in mapper.column_attrs:
        for col in prop.columns:
            length = getattr(col.type, "length", None)
            if isinstance(col.type, LegacyUtf8Mixin) and length:
                event.listen(getattr(class_, prop.key), "set", _length_checker(f"{col.table.name}.{col.name}", length))
