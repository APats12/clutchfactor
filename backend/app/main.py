from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.base import init_db
from app.deps import set_redis_pool
from app.utils.cache import init_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Configure logging
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    # Initialise database
    logger.info("Initialising database connection...")
    init_db(settings.database_url)

    # Initialise Redis
    logger.info("Initialising Redis connection...")
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    set_redis_pool(redis_client)
    init_cache(redis_client)

    logger.info("ClutchFactor backend ready.")
    yield

    # Teardown
    await redis_client.aclose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ClutchFactor API",
        description="NFL live win-probability with SHAP explainability",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all routes
    from app.api.router import api_router
    app.include_router(api_router)

    return app


app = create_app()
