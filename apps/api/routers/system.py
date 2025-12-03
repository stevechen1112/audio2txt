from fastapi import APIRouter, HTTPException

from packages.core.audio2txt.utils.config import Config

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

router = APIRouter(prefix="/system", tags=["system"])

config = Config()


@router.get("/status")
async def system_status():
    """
    Return queue and worker status
    """
    queue_status = {
        "use_celery": config.use_celery,
        "broker": config.celery_broker_url,
        "result_backend": config.celery_result_backend,
        "redis_ping": None,
    }

    if config.use_celery and redis:
        try:
            client = redis.Redis.from_url(config.celery_broker_url, socket_connect_timeout=2)
            queue_status["redis_ping"] = client.ping()
        except Exception as exc:
            queue_status["redis_ping"] = str(exc)

    return {
        "queue": queue_status,
        "notifications": {
            "enabled": config.notification_enabled,
            "webhook_configured": bool(config.notification_webhook_url),
        },
    }
