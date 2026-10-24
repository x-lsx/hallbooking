from ..core.celery_utils import celery_app


@celery_app.task
def login_debug_task(user_id: int, email: str):
    print(f"[CELERY] User logged in: id={user_id}, email={email}")
