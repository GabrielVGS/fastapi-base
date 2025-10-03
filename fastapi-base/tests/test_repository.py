import asyncio
from datetime import datetime, timezone
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


@pytest.mark.asyncio
async def test_paginate_by_time_basic(db_session):
    """Test basic time-based pagination"""
    base_repo = BaseTestRepository(db_session)

    # Create test data with small delays to ensure different timestamps
    users = []
    for i in range(5):
        user_data = BaseTestCreate(name=f"Time User {i}", email=f"timeuser{i}@example.com")
        user = await base_repo.create(user_data)
        users.append(user)
        await asyncio.sleep(0.001)  # Small delay to ensure different timestamps

    # Test first page
    result = await base_repo.paginate_by_time(limit=3)

    assert len(result.items) == 3
    assert result.has_next is True
    assert result.has_previous is False
    assert result.next_cursor is not None
    assert result.previous_cursor is None

    # Verify descending order (newest first)
    for i in range(len(result.items) - 1):
        assert result.items[i].created_at >= result.items[i + 1].created_at


@pytest.mark.asyncio
async def test_paginate_by_time_next_page(db_session):
    """Test getting next page with cursor"""
    base_repo = BaseTestRepository(db_session)

    # Create test data
    for i in range(5):
        user_data = BaseTestCreate(name=f"Next User {i}", email=f"nextuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Get first page
    first_page = await base_repo.paginate_by_time(limit=2)
    assert len(first_page.items) == 2
    assert first_page.has_next is True

    # Get next page
    next_page = await base_repo.paginate_by_time(
        cursor=first_page.next_cursor, limit=2, direction="next"
    )

    assert len(next_page.items) == 2
    assert next_page.has_next is True
    assert next_page.has_previous is True

    # Verify no overlap between pages
    first_page_ids = {item.id for item in first_page.items}
    next_page_ids = {item.id for item in next_page.items}
    assert first_page_ids.isdisjoint(next_page_ids)


@pytest.mark.asyncio
async def test_paginate_by_time_previous_page(db_session):
    """Test getting previous page with cursor"""
    base_repo = BaseTestRepository(db_session)

    # Create test data
    for i in range(5):
        user_data = BaseTestCreate(name=f"Prev User {i}", email=f"prevuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Get first page
    first_page = await base_repo.paginate_by_time(limit=2)

    # Get next page
    next_page = await base_repo.paginate_by_time(
        cursor=first_page.next_cursor, limit=2, direction="next"
    )

    # Get previous page (should match first page)
    prev_page = await base_repo.paginate_by_time(
        cursor=next_page.previous_cursor, limit=2, direction="previous"
    )

    assert len(prev_page.items) == 2
    assert prev_page.has_previous is False
    assert prev_page.has_next is True

    # Items should match first page
    first_page_ids = {item.id for item in first_page.items}
    prev_page_ids = {item.id for item in prev_page.items}
    assert first_page_ids == prev_page_ids


@pytest.mark.asyncio
async def test_paginate_by_time_ascending_order(db_session):
    """Test time-based pagination with ascending order"""
    base_repo = BaseTestRepository(db_session)

    # Create test data
    for i in range(3):
        user_data = BaseTestCreate(name=f"Asc User {i}", email=f"ascuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    result = await base_repo.paginate_by_time(limit=5, sort_order="asc")

    assert len(result.items) >= 3

    # Verify ascending order (oldest first)
    for i in range(len(result.items) - 1):
        assert result.items[i].created_at <= result.items[i + 1].created_at


@pytest.mark.asyncio
async def test_paginate_by_time_with_filters(db_session):
    """Test time-based pagination with additional filters"""
    base_repo = BaseTestRepository(db_session)

    # Create test data with different active states
    for i in range(4):
        user_data = BaseTestCreate(
            name=f"Filter User {i}",
            email=f"filteruser{i}@example.com",
            is_active=i % 2 == 0,  # Alternate between True/False
        )
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Test with filter for active users only
    result = await base_repo.paginate_by_time(limit=10, filters={"is_active": True})

    # Should only get active users
    assert len(result.items) == 2
    for item in result.items:
        assert item.is_active is True


@pytest.mark.asyncio
async def test_paginate_by_time_with_total_count(db_session):
    """Test time-based pagination with total count"""
    base_repo = BaseTestRepository(db_session)

    # Create test data
    for i in range(3):
        user_data = BaseTestCreate(name=f"Count User {i}", email=f"countuser{i}@example.com")
        await base_repo.create(user_data)

    result = await base_repo.paginate_by_time(limit=2, include_total_count=True)

    assert result.total_count is not None
    assert result.total_count >= 3


@pytest.mark.asyncio
async def test_paginate_by_time_invalid_field(db_session):
    """Test time-based pagination with invalid time field"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(RepositoryError, match="Time field 'invalid_field' does not exist"):
        await base_repo.paginate_by_time(time_field="invalid_field")


@pytest.mark.asyncio
async def test_paginate_by_time_result_dict(db_session):
    """Test TimeBasedPaginationResult dict conversion"""
    base_repo = BaseTestRepository(db_session)

    # Create test data
    user_data = BaseTestCreate(name="Dict User", email="dictuser@example.com")
    await base_repo.create(user_data)

    result = await base_repo.paginate_by_time(limit=1)
    result_dict = result.dict()

    assert "items" in result_dict
    assert "has_next" in result_dict
    assert "has_previous" in result_dict
    assert "next_cursor" in result_dict
    assert "previous_cursor" in result_dict
    assert "total_count" in result_dict
    assert "count" in result_dict
    assert result_dict["count"] == len(result.items)


@pytest.mark.asyncio
async def test_get_items_since(db_session):
    """Test getting items since a specific timestamp"""
    base_repo = BaseTestRepository(db_session)

    # Record timestamp before creating items
    before_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create test data
    for i in range(3):
        user_data = BaseTestCreate(name=f"Since User {i}", email=f"sinceuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Get items since the recorded timestamp
    items = await base_repo.get_items_since(since=before_time)

    assert len(items) == 3
    for item in items:
        assert item.created_at >= before_time


@pytest.mark.asyncio
async def test_get_items_since_with_filters(db_session):
    """Test getting items since timestamp with additional filters"""
    base_repo = BaseTestRepository(db_session)

    before_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create test data with different active states
    for i in range(4):
        user_data = BaseTestCreate(
            name=f"Since Filter User {i}",
            email=f"sincefilteruser{i}@example.com",
            is_active=i % 2 == 0,
        )
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Get active items since timestamp
    items = await base_repo.get_items_since(since=before_time, filters={"is_active": True})

    assert len(items) == 2
    for item in items:
        assert item.created_at >= before_time
        assert item.is_active is True


@pytest.mark.asyncio
async def test_get_items_since_with_limit(db_session):
    """Test getting items since timestamp with limit"""
    base_repo = BaseTestRepository(db_session)

    before_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create test data
    for i in range(5):
        user_data = BaseTestCreate(name=f"Limit User {i}", email=f"limituser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    # Get limited items since timestamp
    items = await base_repo.get_items_since(since=before_time, limit=3)

    assert len(items) == 3
    # Should be in ascending order (oldest first)
    for i in range(len(items) - 1):
        assert items[i].created_at <= items[i + 1].created_at


@pytest.mark.asyncio
async def test_get_items_between(db_session):
    """Test getting items between two timestamps"""
    base_repo = BaseTestRepository(db_session)

    # Create item before time range
    early_user = BaseTestCreate(name="Early User", email="early@example.com")
    await base_repo.create(early_user)

    await asyncio.sleep(0.001)
    start_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create items within time range
    for i in range(3):
        user_data = BaseTestCreate(name=f"Between User {i}", email=f"betweenuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    end_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create item after time range
    late_user = BaseTestCreate(name="Late User", email="late@example.com")
    await base_repo.create(late_user)

    # Get items between timestamps
    items = await base_repo.get_items_between(start=start_time, end=end_time)

    assert len(items) == 3
    for item in items:
        assert start_time <= item.created_at <= end_time


@pytest.mark.asyncio
async def test_get_items_between_descending(db_session):
    """Test getting items between timestamps in descending order"""
    base_repo = BaseTestRepository(db_session)

    start_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create test data
    for i in range(3):
        user_data = BaseTestCreate(name=f"Desc User {i}", email=f"descuser{i}@example.com")
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    end_time = datetime.now(timezone.utc)

    # Get items in descending order
    items = await base_repo.get_items_between(start=start_time, end=end_time, sort_order="desc")

    assert len(items) == 3
    # Should be in descending order (newest first)
    for i in range(len(items) - 1):
        assert items[i].created_at >= items[i + 1].created_at


@pytest.mark.asyncio
async def test_get_items_between_with_filters_and_limit(db_session):
    """Test getting items between timestamps with filters and limit"""
    base_repo = BaseTestRepository(db_session)

    start_time = datetime.now(timezone.utc)
    await asyncio.sleep(0.001)

    # Create test data with different active states
    for i in range(6):
        user_data = BaseTestCreate(
            name=f"Filter Between User {i}",
            email=f"filterbetweenuser{i}@example.com",
            is_active=i % 2 == 0,
        )
        await base_repo.create(user_data)
        await asyncio.sleep(0.001)

    end_time = datetime.now(timezone.utc)

    # Get active items with limit
    items = await base_repo.get_items_between(
        start=start_time, end=end_time, filters={"is_active": True}, limit=2
    )

    assert len(items) == 2
    for item in items:
        assert start_time <= item.created_at <= end_time
        assert item.is_active is True


@pytest.mark.asyncio
async def test_time_methods_invalid_field(db_session):
    """Test time-based methods with invalid time field"""
    base_repo = BaseTestRepository(db_session)

    with pytest.raises(RepositoryError, match="Time field 'invalid_field' does not exist"):
        await base_repo.get_items_since(
            since=datetime.now(timezone.utc), time_field="invalid_field"
        )

    with pytest.raises(RepositoryError, match="Time field 'invalid_field' does not exist"):
        await base_repo.get_items_between(
            start=datetime.now(timezone.utc),
            end=datetime.now(timezone.utc),
            time_field="invalid_field",
        )
