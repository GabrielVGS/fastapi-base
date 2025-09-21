# how to create a model


# import the model from this dir
# EXAMPLE
# from .user import User

# where user is something like
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import String, Boolean
# from src.models.base import BaseModel
#
# class User(BaseModel):
#     __tablename__ = "users"
#     username: Mapped[str] = mapped_column(String(50), unique=True)
#     email: Mapped[str] = mapped_column(String(100), unique=True)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# then Generate migration: make alembic-make-migrations
# Apply migration: make alembic-migrate

# from .test import Test
# from .user import User

from .base import Base, BaseModel  # noqa


# from .user import User  # noqa
