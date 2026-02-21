from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ShapFeature(BaseModel):
    feature_name: str
    shap_value: float
    direction: Literal["positive", "negative"]
    display_name: str

    @classmethod
    def from_raw(cls, feature_name: str, shap_value: float, display_name: str) -> "ShapFeature":
        return cls(
            feature_name=feature_name,
            shap_value=shap_value,
            direction="positive" if shap_value >= 0 else "negative",
            display_name=display_name,
        )
