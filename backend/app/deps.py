from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.base import get_session_factory

# ── Settings ──────────────────────────────────────────────────────────────────


def _get_settings() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(_get_settings)]


# ── Database session ──────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Redis client ──────────────────────────────────────────────────────────────

_redis_pool: aioredis.Redis | None = None


def set_redis_pool(pool: aioredis.Redis) -> None:
    global _redis_pool
    _redis_pool = pool


async def get_redis() -> aioredis.Redis:
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialised.")
    return _redis_pool


RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
