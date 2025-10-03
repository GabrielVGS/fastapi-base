import logging
import logging.config
from contextlib import asynccontextmanager

import sentry_sdk
import yaml  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache  # type: ignore
from fastapi_pagination import add_pagination

from src.api import routes
from src.api.deps import get_redis_client
from src.core.backends import RedisBackend
from src.core.config import settings
from src.db.session import add_postgresql_extension


if settings.LOGGING_CONFIG_PATH.exists():
    with open(settings.LOGGING_CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
else:
    print("Warning: logconfig.yml not found")  # pragma: no cover

logger = logging.getLogger(__name__)


tags_metadata = [
    {
        "name": "health",
        "description": "Health check for api",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await add_postgresql_extension()
    redis_client = await get_redis_client()

    # Initialize FastAPI-Cache with Redis backend
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            send_default_pii=True,
            traces_sample_rate=1.0,
            profile_session_sample_rate=1.0,
            profile_lifecycle="trace",
        )
    logger.info("FastAPI app running...")

    yield

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"/{settings.VERSION}/openapi.json",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"])
add_pagination(app)
app.include_router(routes.home_router)
app.include_router(routes.api_router, prefix=f"/{settings.VERSION}")
