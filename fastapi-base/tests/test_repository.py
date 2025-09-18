from typing import Optional

import pytest
import uuid_utils as uuid_ext_pkg
from sqlmodel import Field, SQLModel

from src.core.exceptions import ObjectNotFound, RepositoryError
from src.models.base import BaseModel
from src.repositories.sqlalchemy import BaseSQLAlchemyRepository


class BaseTest(BaseModel, table=True):
    __tablename__ = "test"

    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=100)
    is_active: bool = Field(default=True)


# For test instances
class BaseTestCreate(SQLModel):
    email: str = Field(max_length=255)
    name: str = Field(max_length=100)
    is_active: bool = Field(default=True)


class BaseTestUpdate(SQLModel):
    email: Optional[str] = Field(default=None, max_length=255)
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)


# Concrete Class for testing
class BaseTestRepository(BaseSQLAlchemyRepository[BaseTest, BaseTestCreate, BaseTestUpdate]):
    _model = BaseTest


@pytest.mark.asyncio
async def test_create(db_session):
    """Test create method"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="John Doe", email="john@example.com")
    created_user = await base_repo.create(user_data)

    assert created_user.id is not None
    assert created_user.name == "John Doe"
    assert created_user.email == "john@example.com"
    assert created_user.is_active is True


@pytest.mark.asyncio
async def test_create_many(db_session):
    """Test create_many method"""
    base_repo = BaseTestRepository(db_session)

    users_data = [
        BaseTestCreate(name="User 1", email="user1@example.com"),
        BaseTestCreate(name="User 2", email="user2@example.com"),
        BaseTestCreate(name="User 3", email="user3@example.com"),
        BaseTestCreate(name="User 4", email="user4@example.com"),
    ]

    created_users = await base_repo.create_many(users_data)

    assert len(created_users) == 4
    for i, user in enumerate(created_users, start=1):
        assert user.id is not None
        assert user.name == f"User {i}"
        assert user.email == f"user{i}@example.com"


@pytest.mark.asyncio
async def test_create_many_error(db_session):
    """Test create_many method with duplicate emails to trigger error"""
    base_repo = BaseTestRepository(db_session)

    users_data = [
        BaseTestCreate(name="User 1", email="user1@example.com"),
        BaseTestCreate(name="User 2", email="user1@example.com"),
    ]

    with pytest.raises(RepositoryError):
        await base_repo.create_many(users_data)


@pytest.mark.asyncio
async def test_get_not_found(db_session):
    """Test getting an instance that does not exist"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(ObjectNotFound):
        await base_repo.get(id=uuid_ext_pkg.uuid7())  # Assuming this ID does not exist
        # Spoiler: it doesn’t exist (unless my cat ran the tests)


@pytest.mark.asyncio
async def test_get_sqlalchemy_error(db_session):
    """Test getting an instance with invalid criteria to trigger SQLAlchemy error"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(RepositoryError):
        # Intentionally passing an invalid filter to trigger an error
        await base_repo.get(invalid_field="some_value")  # type: ignore


@pytest.mark.asyncio
async def test_get_with_relations(db_session):
    """Test getting a user with relations (even though there are none in this simple model)"""
    base_repo = BaseTestRepository(db_session)
    user_data = BaseTestCreate(name="Relational User", email="relational@example.com")
    created_user = await base_repo.create(user_data)

    # Fix: Pass an empty list for relations as the first parameter, then the ID as a keyword argument
    found_user = await base_repo.get_with_relations(relations=[], id=created_user.id)

    assert found_user.id == created_user.id
    assert found_user.name == "Relational User"
    assert found_user.email == "relational@example.com"


@pytest.mark.asyncio
async def test_get_inexistent_relations(db_session):
    """Test getting a user with non-existent relations (should be silently ignored)"""
    base_repo = BaseTestRepository(db_session)
    user_data = BaseTestCreate(name="No Relations User", email="no_relations@example.com")
    created_user = await base_repo.create(user_data)

    # Non-existent relations should be silently ignored
    found_user = await base_repo.get_with_relations(
        relations=["non_existent_relation"], id=created_user.id
    )

    # Should still return the user, just without the non-existent relation loaded
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.name == "No Relations User"
    assert found_user.email == "no_relations@example.com"


@pytest.mark.asyncio
async def test_update_by_id(db_session):
    """Test updating a user by ID"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Initial Name", email="initial@example.com")
    created_user = await base_repo.create(user_data)
    update_data = BaseTestUpdate(name="Updated Name")
    updated_user = await base_repo.update_by_id(created_user.id, update_data)
    assert updated_user.name == "Updated Name"
    assert updated_user.email == "initial@example.com"


@pytest.mark.asyncio
async def test_update_not_found(db_session):
    """Test updating a non-existent user by ID"""
    base_repo = BaseTestRepository(db_session)

    update_data = BaseTestUpdate(name="Should Not Exist")

    with pytest.raises(ObjectNotFound):
        await base_repo.update_by_id(uuid_ext_pkg.uuid7(), update_data)  # Non-existent ID


@pytest.mark.asyncio
async def test_get_user(db_session):
    """Test getting a user by criteria"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Jane Doe", email="jane@example.com")
    created_user = await base_repo.create(user_data)

    found_user = await base_repo.get(email="jane@example.com")
    assert found_user.id == created_user.id
    assert found_user.name == "Jane Doe"


@pytest.mark.asyncio
async def test_update_user(db_session):
    """Test updating a user"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Bob Smith", email="bob@example.com")
    created_user = await base_repo.create(user_data)

    update_data = BaseTestUpdate(name="Robert Smith")
    updated_user = await base_repo.update(created_user, update_data)

    assert updated_user.name == "Robert Smith"
    assert updated_user.email == "bob@example.com"  # Should remain unchanged


@pytest.mark.asyncio
async def test_delete_by_id(db_session):
    """Test deleting a user by ID"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Delete Me", email="delete@example.com")
    created_user = await base_repo.create(user_data)
    await base_repo.delete_by_id(created_user.id)

    with pytest.raises(ObjectNotFound):
        await base_repo.get(id=created_user.id)


@pytest.mark.asyncio
async def test_delete_by_id_sqlalchemy_error(db_session):
    """Test deleting a user by ID with invalid ID to trigger SQLAlchemy error"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(RepositoryError):
        await base_repo.delete_by_id("invalid-uuid")  # type: ignore


@pytest.mark.asyncio
async def test_soft_delete_by_id(db_session):
    """Test soft deleting a user by ID"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Soft Delete Me", email="softdelete@example.com")
    created_user = await base_repo.create(user_data)
    await base_repo.soft_delete(created_user.id)
    soft_deleted_user = await base_repo.get(id=created_user.id)
    assert soft_deleted_user.deleted_at is not None


@pytest.mark.asyncio
async def test_soft_delete_by_id_not_found(db_session):
    """Test soft deleting a non-existent user by ID"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(ObjectNotFound):
        await base_repo.soft_delete(uuid_ext_pkg.uuid7())  # Non-existent ID


@pytest.mark.asyncio
async def test_delete_user(db_session):
    """Test deleting a user"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Delete Me", email="delete@example.com")
    created_user = await base_repo.create(user_data)

    await base_repo.delete(id=created_user.id)

    with pytest.raises(ObjectNotFound):
        await base_repo.get(id=created_user.id)


@pytest.mark.asyncio
async def test_exists(db_session):
    """Test exists method"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Existence Check", email="existence@example.com")
    _ = await base_repo.create(user_data)
    exists = await base_repo.exists(email="existence@example.com")
    not_exists = await base_repo.exists(email="nonexistent@example.com")

    assert exists is True
    assert not_exists is False


@pytest.mark.asyncio
async def test_count(db_session):
    """Test count method"""
    base_repo = BaseTestRepository(db_session)

    initial_count = await base_repo.count()

    user_data = BaseTestCreate(name="Count Me", email="countme@example.com")
    await base_repo.create(user_data)
    new_count = await base_repo.count()
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_filter_by(db_session):
    """Test filter_by method"""
    base_repo = BaseTestRepository(db_session)

    for i in range(10):
        data = BaseTestCreate(name=f"User {i}", email=f"user{i}@example.com")
        await base_repo.create(data)

    result1 = await base_repo.filter_by(filters={"email": "user5@example.com", "name": "User 5"})

    assert len(result1) == 1
    assert result1[0].email == "user5@example.com"

    result2 = await base_repo.filter_by(filters={"is_active": True}, limit=5)

    assert len(result2) == 5
    for user in result2:
        assert user.is_active is True


@pytest.mark.asyncio
async def test_all_users(db_session):
    """Test getting all users with pagination"""
    base_repo = BaseTestRepository(db_session)

    for i in range(3):
        user_data = BaseTestCreate(name=f"User {i}", email=f"user{i}@example.com")
        await base_repo.create(user_data)

    all_users = await base_repo.all(limit=10, sort_field="name", sort_order="asc")

    assert len(all_users) == 3
    assert all_users[0].name == "User 0"


@pytest.mark.asyncio
async def test_filter_users(db_session):
    """Test filtering users with the f() method"""
    base_repo = BaseTestRepository(db_session)

    active_user = BaseTestCreate(name="Active User", email="active@example.com", is_active=True)
    inactive_user = BaseTestCreate(
        name="Inactive User", email="inactive@example.com", is_active=False
    )

    await base_repo.create(active_user)
    await base_repo.create(inactive_user)

    active_users = await base_repo.f(is_active=True)
    assert len(active_users) == 1
    assert active_users[0].name == "Active User"


@pytest.mark.asyncio
async def test_get_or_create(db_session):
    """Test get_or_create functionality"""
    base_repo = BaseTestRepository(db_session)

    user_data = BaseTestCreate(name="Get Or Create", email="getorcreate@example.com")

    user1, created = await base_repo.get_or_create(user_data, email="getorcreate@example.com")
    assert user1.id is not None
    assert created is True

    user2, created = await base_repo.get_or_create(user_data, email="getorcreate@example.com")
    assert user1.id == user2.id
    assert created is False


def test_repository_initialization(db_session):
    """Test that repository can be initialized properly"""
    base_repo = BaseTestRepository(db_session)

    assert base_repo.db == db_session
    assert base_repo._model == BaseTest
