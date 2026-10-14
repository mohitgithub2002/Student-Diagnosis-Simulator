from celery import Celery

from app.core.config import get_settings
from app.workers import jobs

settings = get_settings()
celery_app = Celery("sds", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="Asia/Kolkata",
    beat_schedule={
        "sweep-withdrawals-daily": {"task": "sds.sweep_withdrawals", "schedule": 24 * 60 * 60},
    },
)

for _name, _fn in jobs.JOBS.items():
    celery_app.task(name=f"sds.{_name}")(_fn)
