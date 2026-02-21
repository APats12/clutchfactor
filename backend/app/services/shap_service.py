from __future__ import annotations

import logging

import numpy as np
import shap

from app.ml.features import FEATURE_COLS, FEATURE_DISPLAY_NAMES
from app.ml.registry import get_xgb_model
from app.schemas.shap import ShapFeature

logger = logging.getLogger(__name__)

# Cache the SHAP explainer since building it from the booster takes ~100ms
_explainer_cache: dict[int, shap.TreeExplainer] = {}


def _get_explainer(model) -> shap.TreeExplainer:
    # Unwrap CalibratedClassifierCV to get the raw XGBoost model for Tree SHAP
    xgb = get_xgb_model(model)
    key = id(xgb)
    if key not in _explainer_cache:
        logger.info("Building SHAP TreeExplainer (first call, then cached)...")
        _explainer_cache[key] = shap.TreeExplainer(xgb)
    return _explainer_cache[key]


class ShapService:
    def explain(
        self,
        features: np.ndarray,
        model,
        top_n: int = 5,
    ) -> list[ShapFeature]:
        """
        Compute SHAP values for a (1, 10) feature array.
        Returns top_n features sorted by absolute SHAP value descending.
        """
        explainer = _get_explainer(model)

        # shap_values returns shape (1, 10) for binary XGBoost (log-odds space)
        sv = explainer.shap_values(features)
        if isinstance(sv, list):
            # Older shap versions return list of arrays for binary classification
            sv = sv[1]
        sv = np.array(sv).flatten()  # shape (10,)

        results: list[ShapFeature] = []
        for i, col in enumerate(FEATURE_COLS):
            results.append(
                ShapFeature.from_raw(
                    feature_name=col,
                    shap_value=float(sv[i]),
                    display_name=FEATURE_DISPLAY_NAMES.get(col, col),
                )
            )

        results.sort(key=lambda f: abs(f.shap_value), reverse=True)
        return results[:top_n]
