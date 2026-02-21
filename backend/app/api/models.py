from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.models.model_version import ModelVersion
from app.deps import DbSession
from app.schemas.model_version import ModelVersionRead

router = APIRouter(tags=["models"])


@router.get("/models/current", response_model=ModelVersionRead)
async def get_current_model(db: DbSession) -> ModelVersionRead:
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_current.is_(True))
    )
    mv = result.scalar_one_or_none()
    if mv is None:
        raise HTTPException(status_code=404, detail="No current model version found. Run `make train` first.")
    return ModelVersionRead.model_validate(mv)
