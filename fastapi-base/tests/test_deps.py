import pytest
import redis.asyncio as Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_redis_client


@pytest.mark.asyncio
async def test_get_redis_client():
    """Test that get_redis_client yields a Redis client"""
    redis_client = await get_redis_client()
    assert isinstance(redis_client, Redis.Redis)
    # Optionally test ping
    pong = await redis_client.ping()
    assert pong is True
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_get_db():
    """Test that get_db yields an AsyncSession"""
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        await session.close()
