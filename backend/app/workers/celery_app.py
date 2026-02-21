from __future__ import annotations

from celery import Celery

from app.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "clutchfactor",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.workers.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
    return app


celery_app = create_celery()
