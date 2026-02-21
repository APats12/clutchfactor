from __future__ import annotations

import json

import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None

LATEST_EVENT_TTL = 3600  # 1 hour


def init_cache(redis_client: aioredis.Redis) -> None:
    global _redis
    _redis = redis_client


def _key(game_id: str) -> str:
    return f"game:{game_id}:latest"


async def set_latest_game_event(game_id: str, event: dict) -> None:
    if _redis is None:
        return
    await _redis.set(_key(game_id), json.dumps(event), ex=LATEST_EVENT_TTL)


async def get_latest_game_event(game_id: str) -> str | None:
    if _redis is None:
        return None
    return await _redis.get(_key(game_id))
