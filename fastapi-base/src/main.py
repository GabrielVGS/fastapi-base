import logging
import logging.config

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

app = FastAPI(
    title="fastapi-base",
    description="base project for fastapi backend",
    version=settings.VERSION,
    openapi_url=f"/{settings.VERSION}/openapi.json",
    openapi_tags=tags_metadata,
)


# pragma: no cover start
async def on_startup() -> None:
    await add_postgresql_extension()
    redis_client = await get_redis_client()

    # Initialize FastAPI-Cache with Redis backend
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            # Add data like request headers and IP for users,
            # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            # Set profile_session_sample_rate to 1.0 to profile 100%
            # of profile sessions.
            profile_session_sample_rate=1.0,
            # Set profile_lifecycle to "trace" to automatically
            # run the profiler on when there is an active transaction
            profile_lifecycle="trace",
        )
    logger.info("FastAPI app running...")


# pragma: no cover stop


app.add_middleware(CORSMiddleware, allow_origins=["*"])

app.add_event_handler("startup", on_startup)

add_pagination(app)

app.include_router(routes.home_router)
app.include_router(routes.api_router, prefix=f"/{settings.VERSION}")
