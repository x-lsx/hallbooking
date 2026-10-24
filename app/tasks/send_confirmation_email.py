import asyncio
import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.celery_utils import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = settings.EMAIL_USERNAME
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_USERNAME,
        password=settings.EMAIL_PASSWORD,
        use_tls=True,
    )


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5, "countdown": 60},
)
def send_confirmation_email(to_email: str, verify_url: str):
    try:
        asyncio.run(
            send_email(
                to_email=to_email,
                subject="Подтвердите ваш email",
                body=f"Пожалуйста, подтвердите email по ссылке: {verify_url}",
            )
        )
        logger.info(f"Письмо отправлено на {to_email}")
    except Exception as e:
        logger.error(f"Ошибка отправки на {to_email}: {e}")
        raise

