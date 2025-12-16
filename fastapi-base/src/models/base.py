import uuid
from datetime import datetime, timezone
from typing import Optional

import uuid_utils as uuid_ext_pkg
from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import expression


# https://docs.sqlalchemy.org/en/20/core/compiler.html#utc-timestamp-function
class utcnow(expression.FunctionElement):  # type: ignore
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw) -> str:  # type: ignore
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


# Create the declarative base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# this is the base model, as a best practice, other db models should inherit it
class BaseModel(Base):
    """Base model with common fields for all database tables."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        unique=True,
        default=uuid_ext_pkg.uuid7,
        server_default=text("uuidv7()"),
    )

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
