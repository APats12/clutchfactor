from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WpPrediction(Base):
    __tablename__ = "wp_predictions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    play_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plays.id"), index=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_versions.id"), index=True
    )
    home_wp: Mapped[float] = mapped_column(Float)
    away_wp: Mapped[float] = mapped_column(Float)
    predicted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    play: Mapped["Play"] = relationship("Play", back_populates="wp_predictions")  # noqa: F821
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion")  # noqa: F821
    shap_values: Mapped[list["ShapValue"]] = relationship(  # noqa: F821
        "ShapValue", back_populates="wp_prediction"
    )
