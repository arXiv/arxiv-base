"""Custom SQLAlchemy types for handling mixed latin1/utf8 encoding in legacy databases.

These TypeDecorators handle transcoding from bytes to strings based on the column's character set.
"""

from typing import Optional, Any, Type
from sqlalchemy import TypeDecorator, String, Text, LargeBinary, func
from sqlalchemy.sql.type_api import _CT, ColumnElement, TypeEngine
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.dialects import mysql
from sqlalchemy.types import UserDefinedType
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
        return operator(func.binary(self.expr), func.binary(other))

    def contains(self, other: Any, **kwargs: Any) -> Any:
        """Override contains to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        # Use LIKE with BINARY
        pattern = b'%' + other + b'%'
        return func.binary(self.expr).like(func.binary(pattern))

    def startswith(self, other: Any, escape: Optional[str] = None, autoescape: bool = False) -> Any:
        """Override startswith to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        pattern = other + b'%'
        return func.binary(self.expr).like(func.binary(pattern))

    def endswith(self, other: Any, escape: Optional[str] = None, autoescape: bool = False) -> Any:
        """Override endswith to work with binary data."""
        if isinstance(other, str):
            other = other.encode('utf-8')
        pattern = b'%' + other
        return func.binary(self.expr).like(func.binary(pattern))


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
        return func.binary(bindvalue)

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
        return func.binary(bindvalue)

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