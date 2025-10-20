"""
Cross-database type utilities for SQLAlchemy models
"""

import uuid

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


class UUID(TypeDecorator):
    """
    Cross-database UUID column type.
    Uses PostgreSQL UUID for PostgreSQL databases, String for SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            # For SQLite and other databases, use String(36) to store UUID as text
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For SQLite, convert UUID to string
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For SQLite, convert string back to UUID
            if isinstance(value, str):
                return uuid.UUID(value)
            else:
                return value


class JSON(TypeDecorator):
    """
    Cross-database JSON column type.
    Uses PostgreSQL JSON for PostgreSQL databases, Text for SQLite.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSON as PostgresJSON

            return dialect.type_descriptor(PostgresJSON())
        else:
            # For SQLite, use Text and handle JSON serialization manually
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For SQLite, serialize to JSON string
            import json

            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For SQLite, deserialize from JSON string
            import json

            if isinstance(value, str):
                return json.loads(value)
            else:
                return value
