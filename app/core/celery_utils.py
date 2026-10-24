from celery import Celery

from .config import settings

celery_app = Celery(
    "authapp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_URL,
    include=["app.tasks.send_confirmation_email",
             "app.tasks.send_reset_password_email",
             "app.tasks.test"
             ],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'], 
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,        # 1 час
    task_soft_time_limit=3300,
)
