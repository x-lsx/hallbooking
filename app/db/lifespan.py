import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.exceptions import ConnectionError
from sqlalchemy import text

from .postgres import engine
from .redis import redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL подключен успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к PostgreSQL: {e}")
        raise
    try:
        await redis_client.ping()
        logger.info("Redis подключен успешно")
    except ConnectionError as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        raise

    yield

    logger.info("Завершение работы приложения")
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Все соединения закрыты")
