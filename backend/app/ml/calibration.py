"""
Calibrated model wrapper: XGBoost + isotonic regression.

Defined here (not in train.py) so joblib can unpickle it
in any process via the stable path ``app.ml.calibration._CalibratedModel``.
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from xgboost import XGBClassifier


class _CalibratedModel:
    """Thin wrapper: XGBoost raw output → isotonic calibration → probability."""

    def __init__(self, xgb: XGBClassifier, iso: IsotonicRegression) -> None:
        self.xgb = xgb
        self.iso = iso

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw = self.xgb.predict_proba(X)[:, 1]
        cal = self.iso.predict(raw)
        return np.column_stack([1.0 - cal, cal])
