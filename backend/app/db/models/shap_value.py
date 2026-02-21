from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShapValue(Base):
    __tablename__ = "shap_values"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    wp_prediction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wp_predictions.id"), index=True
    )
    feature_name: Mapped[str]
    shap_value: Mapped[float] = mapped_column(Float)

    wp_prediction: Mapped["WpPrediction"] = relationship(  # noqa: F821
        "WpPrediction", back_populates="shap_values"
    )
