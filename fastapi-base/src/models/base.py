import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression


# https://docs.sqlalchemy.org/en/20/core/compiler.html#utc-timestamp-function
class utcnow(expression.FunctionElement):  # type: ignore
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw) -> str:  # type: ignore
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


# SQLAlchemy declarative base
Base = declarative_base()


# this is the base model, as a best practice, other db models should inherit it
class BaseModel(Base):  # type: ignore
    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        unique=True,
        index=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=utcnow(),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=utcnow(),
        nullable=True,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
