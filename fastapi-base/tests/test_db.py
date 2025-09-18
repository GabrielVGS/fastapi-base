import pytest

from src.db.init_db import create_init_data
from src.db.session import AsyncSessionLocal as SessionLocal
from src.db.session import add_postgresql_extension, get_session


@pytest.mark.asyncio
async def test_create_init_data():
    """Test the create_init_data function"""
    result = await create_init_data()
    assert result is None  # Assuming the function returns None on success


@pytest.mark.asyncio
async def test_session_local():
    """Test the AsyncSessionLocal creation"""
    async with SessionLocal() as session:
        assert session is not None
        assert hasattr(session, "execute")
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")
        assert hasattr(session, "close")


def test_get_session():
    """Test the get_session dependency"""
    gen = get_session()
    assert hasattr(gen, "__aiter__")
    assert hasattr(gen, "__anext__")


@pytest.mark.asyncio
async def test_add_postgresql_extension():
    """Test the add_postgresql_extension function"""
    await add_postgresql_extension()
    # If no exception is raised, we assume success
