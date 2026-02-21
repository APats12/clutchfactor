from __future__ import annotations

import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://cf:changeme@localhost:5432/clutchfactor"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ML
    model_artifact_dir: str = "./ml/artifacts"

    # Replay
    replay_speed_plays_per_sec: float = 1.0
    replay_default_seasons: list[int] = [2021, 2022, 2023]

    # Security / CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    secret_key: str = "change-this-to-a-random-secret"

    # Logging
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
