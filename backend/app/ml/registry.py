"""
Model registry: loads and caches the current model artifact.

Supports two artifact formats:
  .joblib  — CalibratedClassifierCV wrapping XGBoost (current default)
  .ubj     — Raw XGBoost native format (legacy)

The module-level singleton avoids reloading on every request.
Cache is invalidated by calling `invalidate()`.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

_cached_model = None  # CalibratedClassifierCV | XGBClassifier
_cached_version_id: uuid.UUID | None = None
_cached_version_name: str | None = None


async def get_current() -> tuple:
    """
    Returns (model, model_version_id, model_version_name).

    model is either a CalibratedClassifierCV (.joblib) or XGBClassifier (.ubj).
    Both expose .predict_proba(). Use get_xgb_model(model) for Tree SHAP.
    """
    global _cached_model, _cached_version_id, _cached_version_name

    if _cached_model is not None and _cached_version_id is not None:
        return _cached_model, _cached_version_id, _cached_version_name

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import get_settings
    from app.db.models.model_version import ModelVersion

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        result = await session.execute(
            select(ModelVersion).where(ModelVersion.is_current.is_(True))
        )
        mv = result.scalar_one_or_none()

    await engine.dispose()

    if mv is None:
        raise RuntimeError(
            "No current model version in database. Run `make train` to train a model."
        )

    artifact_path = Path(settings.model_artifact_dir) / Path(mv.artifact_path).name
    if not artifact_path.exists():
        raise RuntimeError(
            f"Model artifact not found at {artifact_path}. "
            "Ensure ml/artifacts/ is mounted or run `make train`."
        )

    logger.info("Loading model artifact: %s", artifact_path)
    model = _load_artifact(artifact_path)

    _cached_model = model
    _cached_version_id = mv.id
    _cached_version_name = mv.name

    logger.info("Model '%s' loaded and cached.", mv.name)
    return model, mv.id, mv.name


def _load_artifact(path: Path):
    """Load a model artifact based on its file extension."""
    suffix = path.suffix.lower()
    if suffix == ".joblib":
        import joblib
        from app.ml.calibration import _CalibratedModel  # noqa: F401 — needed for unpickling
        return joblib.load(str(path))
    elif suffix == ".ubj":
        model = XGBClassifier()
        model.load_model(str(path))
        return model
    else:
        raise RuntimeError(f"Unrecognised model artifact format: {suffix}")


def get_xgb_model(model) -> XGBClassifier:
    """
    Extract the underlying XGBClassifier for Tree SHAP.

    Handles:
      - _CalibratedModel (train.py wrapper): has .xgb attribute
      - CalibratedClassifierCV (sklearn): has .calibrated_classifiers_
      - Raw XGBClassifier: returned as-is
    """
    # Our custom calibrated wrapper
    if hasattr(model, "xgb"):
        return model.xgb
    # sklearn CalibratedClassifierCV (legacy)
    if hasattr(model, "calibrated_classifiers_"):
        return model.calibrated_classifiers_[0].estimator
    # Raw XGBClassifier
    if isinstance(model, XGBClassifier):
        return model
    raise TypeError(f"Cannot extract XGBClassifier from {type(model)}")


def invalidate() -> None:
    """Force reload on next get_current() call."""
    global _cached_model, _cached_version_id, _cached_version_name
    _cached_model = None
    _cached_version_id = None
    _cached_version_name = None
    logger.info("Model cache invalidated.")
