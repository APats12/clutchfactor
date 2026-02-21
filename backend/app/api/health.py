from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.deps import DbSession, RedisDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: DbSession, redis: RedisDep) -> dict:
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"

    # Check Redis
    try:
        await redis.ping()
        redis_status = "connected"
    except Exception as exc:
        redis_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" and redis_status == "connected" else "degraded",
        "db": db_status,
        "redis": redis_status,
    }
