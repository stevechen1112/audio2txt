"""
Celery application bootstrap for Audio2txt Enterprise
"""
from celery import Celery

from packages.core.audio2txt.utils.config import Config

config = Config()

celery_app = Celery(
    "audio2txt",
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
)

celery_app.conf.update(
    task_default_queue="transcription",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
