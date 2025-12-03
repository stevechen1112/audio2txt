"""
Celery tasks for long-running processing jobs
"""
import asyncio

from .celery_app import celery_app
from .services import ProcessingService

service = ProcessingService.get_instance()


@celery_app.task(name="audio2txt.process_audio")
def process_audio_task(task_id: str, file_path: str, template_id: str) -> str:
    """
    Celery wrapper for the async processing service
    """
    asyncio.run(service.process_audio(task_id, file_path, template_id))
    return task_id
