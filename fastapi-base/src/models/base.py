import uuid
from datetime import datetime, timezone
from typing import Optional

import uuid_utils as uuid_ext_pkg
from sqlalchemy import text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import expression
from sqlmodel import Column, DateTime, Field, SQLModel


# https://docs.sqlalchemy.org/en/20/core/compiler.html#utc-timestamp-function
class utcnow(expression.FunctionElement):  # type: ignore
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw) -> str:  # type: ignore
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


# this is the base model, as a best practice, other db models should inherit it
class BaseModel(SQLModel):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid_ext_pkg.uuid7,
        primary_key=True,
        index=True,
        sa_column_kwargs={"server_default": text("uuidv7()"), "unique": True},
    )

    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=utcnow(),
            nullable=True,
        ),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=utcnow(),
            nullable=True,
        ),
    )

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
        ),
    )
