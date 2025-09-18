import asyncio
import logging

from src.db.session import AsyncSessionLocal as SessionLocal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_init_data() -> None:
    async with SessionLocal() as session:
        # Add initial data here
        # Example:
        # user1 = User(name="John Doe", email="john@example.com")
        # user2 = User(name="Jane Smith", email="jane@example.com")
        # session.add(user1)
        # session.add(user2)

        await session.commit()


# pragma: no cover start
async def main() -> None:
    logger.info("Creating initial data")
    await create_init_data()
    logger.info("Initial data created")


# pragma: no cover stop

if __name__ == "__main__":
    asyncio.run(main())  # pragma: no cover
