from fastapi import APIRouter

from app.api import games, health, models, predictions, replay, stream

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(games.router)
api_router.include_router(predictions.router)
api_router.include_router(models.router)
api_router.include_router(stream.router)
api_router.include_router(replay.router)
