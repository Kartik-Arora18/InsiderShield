from celery import Celery
from app.core.config import settings

celery_app = Celery("insidershield", broker=settings.redis_url, backend=settings.redis_url, include=["app.worker.tasks"])
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="UTC", enable_utc=True, task_acks_late=True,
    task_reject_on_worker_lost=True, worker_prefetch_multiplier=1,
    task_track_started=True, broker_connection_retry_on_startup=True,
    beat_schedule={"dispatch-outbox-every-five-seconds": {
        "task": "app.worker.tasks.dispatch_outbox", "schedule": 5.0
    }},
)
