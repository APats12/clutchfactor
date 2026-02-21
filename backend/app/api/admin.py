from __future__ import annotations

from fastapi import APIRouter
from app.db.seed import seed

router = APIRouter(tags=["admin"])


@router.post("/admin/seed")
async def run_seed() -> dict:
    await seed()
    return {"status": "ok"}
