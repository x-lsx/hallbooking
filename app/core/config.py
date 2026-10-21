import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ====================== Основные ======================
    APP_NAME: str = Field(default="FastAPI Cost-Calculator")
    DEBUG: bool = Field(default=True)
    ENV: str = Field(default="local")  # docker, local, test, production
    LOG_LEVEL: str = Field(default="INFO")

    # ====================== Базы данных ======================
    POSTGRES_URL: str = Field(..., description="Обязательная переменная")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: str = Field(default="")

    CELERY_BROKER_URL: str = Field(...)
    CELERY_RESULT_URL: str = Field(...)

    # ====================== JWT Security ======================
    ACCESS_SECRET_KEY: str = Field(..., description="Обязательный ключ")
    REFRESH_SECRET_KEY: str = Field(..., description="Обязательный ключ")
    JWT_ALGORITHM: str = Field(default="HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # ====================== CORS ======================
    CORS_ORIGINS: str = Field(
        "",
        alias="CORS_ORIGINS",
        description="Список разрешенных доменов для CORS, разделенных запятыми",
    )

    # ====================== Пути ======================
    STATIC_DIR: Path = BASE_DIR / "static"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"

    # ====================== Email ======================
    EMAIL_HOST: str = Field(..., description="SMTP server host")
    EMAIL_PORT: int = Field(..., description="SMTP server port")
    EMAIL_USERNAME: str = Field(..., description="Email username")
    EMAIL_PASSWORD: str = Field(..., description="Email password")

    # ====================== Verification Token ======================
    API_URL: str = Field(..., description="Base URL of the API")
    FRONTEND_URL: str = Field(..., description="Base URL of the frontend")
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(
        default=1, description="Verification token expiration time in hours"
    )
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(
        default=1, description="Password reset token expiration time in hours"
    )

    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env"
            if os.getenv("ENV") == "docker"
            else BASE_DIR / ".env.local"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
