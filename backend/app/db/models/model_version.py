from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    artifact_path: Mapped[str] = mapped_column(Text)
    brier_score: Mapped[float | None] = mapped_column(Float)
    log_loss_val: Mapped[float | None] = mapped_column(Float)
    trained_on_seasons: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<ModelVersion {self.name} current={self.is_current}>"
