"""
Celery tasks for asynchronous SHAP computation.

For replay/developer mode, SHAP is computed synchronously in the request loop
(fast enough at < 10ms per play).

This module is reserved for future live-mode use where SHAP latency would
block the main asyncio event loop.
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="compute_shap_async")
def compute_shap_async(self, wp_prediction_id: str) -> dict:
    """
    Compute and persist SHAP values for a given WpPrediction ID.
    Called asynchronously by Celery workers in live mode.
    """
    try:
        result = asyncio.run(_compute_and_persist(uuid.UUID(wp_prediction_id)))
        return {"status": "ok", "wp_prediction_id": wp_prediction_id, **result}
    except Exception as exc:
        logger.exception("SHAP task failed for %s", wp_prediction_id)
        raise self.retry(exc=exc, countdown=5, max_retries=3) from exc


async def _compute_and_persist(wp_prediction_id: uuid.UUID) -> dict:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import get_settings
    from app.db.models.shap_value import ShapValue
    from app.db.models.wp_prediction import WpPrediction
    from app.ml.features import FEATURE_COLS, extract_features
    from app.ml.registry import get_current
    from app.services.shap_service import ShapService

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        wp_pred = (
            await session.execute(
                select(WpPrediction).where(WpPrediction.id == wp_prediction_id)
            )
        ).scalar_one_or_none()

        if wp_pred is None:
            return {"error": "WpPrediction not found"}

        # Get the play to reconstruct features
        from app.db.models.play import Play
        play = (
            await session.execute(select(Play).where(Play.id == wp_pred.play_id))
        ).scalar_one_or_none()

        if play is None:
            return {"error": "Play not found"}

        play_dict = {
            "down": play.down,
            "yards_to_go": play.yards_to_go,
            "yardline_100": 100 - play.yard_line_from_own if play.yard_line_from_own else None,
            "qtr": play.quarter,
            "game_seconds_remaining": play.game_clock_seconds,
            "score_differential": play.score_home - play.score_away,
            "posteam_timeouts_remaining": 3,  # simplified
            "defteam_timeouts_remaining": 3,
            "half_seconds_remaining": play.game_clock_seconds,
            "spread_line": 0.0,
        }
        features = extract_features(play_dict)
        model, _, _ = await get_current()
        shap_svc = ShapService()
        shap_features = shap_svc.explain(features, model, top_n=len(FEATURE_COLS))

        # Persist all SHAP values
        for sf in shap_features:
            sv = ShapValue(
                id=uuid.uuid4(),
                wp_prediction_id=wp_prediction_id,
                feature_name=sf.feature_name,
                shap_value=sf.shap_value,
            )
            session.add(sv)
        await session.commit()

    await engine.dispose()
    return {"shap_values_count": len(shap_features)}
