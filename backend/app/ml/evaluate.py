from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Return Brier score and log loss for evaluation."""
    return {
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob)),
    }


def calibration_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict[str, list[float]]:
    """Return fraction_of_positives and mean_predicted_value for a calibration curve."""
    fraction_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    return {
        "fraction_of_positives": fraction_pos.tolist(),
        "mean_predicted_value": mean_pred.tolist(),
    }
