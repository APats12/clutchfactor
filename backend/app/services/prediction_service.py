from __future__ import annotations

import uuid
from datetime import datetime, timezone

import numpy as np

from app.ml.features import extract_features
from app.ml.registry import get_current
from app.schemas.prediction import PredictRequest, PredictResponse
from app.schemas.shap import ShapFeature


class PredictionService:
    async def predict_and_explain(
        self,
        request: PredictRequest,
        shap_svc: "ShapService",  # noqa: F821
    ) -> PredictResponse:
        model, version_id, version_name = await get_current()

        # Build feature vector from request
        play_dict = {
            "down": request.down,
            "yards_to_go": request.yards_to_go,
            "yardline_100": request.yardline_100,
            "qtr": request.qtr,
            "game_seconds_remaining": request.game_seconds_remaining,
            "score_differential": request.score_differential,
            "posteam_timeouts_remaining": request.posteam_timeouts_remaining,
            "defteam_timeouts_remaining": request.defteam_timeouts_remaining,
            "half_seconds_remaining": request.half_seconds_remaining,
            "spread_line": request.spread_line,
        }
        features = extract_features(play_dict)

        # XGBoost: predict_proba returns [[away_prob, home_prob]]
        proba = model.predict_proba(features)[0]
        home_wp = float(proba[1])
        away_wp = float(1.0 - home_wp)

        # SHAP explanation
        top_shap = shap_svc.explain(features, model)

        # Ad-hoc /predict calls are ephemeral — replay handles DB persistence.
        return PredictResponse(
            play_id=uuid.uuid4(),
            home_wp=home_wp,
            away_wp=away_wp,
            model_version=version_name,
            top_shap=top_shap,
            predicted_at=datetime.now(tz=timezone.utc),
        )

    async def predict_raw(
        self,
        features: np.ndarray,
        model,
    ) -> tuple[float, float]:
        """
        Lower-level prediction used by ReplayService.
        Returns (home_wp, away_wp).
        """
        proba = model.predict_proba(features)[0]
        return float(proba[1]), float(1.0 - proba[1])
