from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.prediction_service import PredictionService
from app.services.shap_service import ShapService

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> PredictResponse:
    try:
        pred_svc = PredictionService()
        shap_svc = ShapService()
        return await pred_svc.predict_and_explain(request, shap_svc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
