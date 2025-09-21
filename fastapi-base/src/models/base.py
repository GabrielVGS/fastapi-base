import uuid
from datetime import datetime, timezone
from typing import Optional

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


# SQLAlchemy 2.0 declarative base
class Base(DeclarativeBase):
    pass


# this is the base model, as a best practice, other db models should inherit it
class BaseModel(Base):
    __abstract__ = True

    id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        unique=True,
        index=True,
    )

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=utcnow(),
        nullable=True,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=utcnow(),
        nullable=True,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
