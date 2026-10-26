import os
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Основные
    APP_NAME: str = "Zalbook"
    DEBUG: bool = False
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    POSTGRES_URL: str  

    REDIS_URL: str 
    REDIS_HOST: str 
    REDIS_PORT: int 
    REDIS_PASSWORD: str 

    CELERY_BROKER_URL: str 
    CELERY_RESULT_URL: str
    
    # JWT
    ACCESS_SECRET_KEY: SecretStr
    REFRESH_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS и сеть
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = ""        
    TRUSTED_PROXIES: str = ""     

    # Почта 
    EMAIL_HOST: str | None = None
    EMAIL_PORT: int = 465
    EMAIL_USERNAME: str | None = None
    EMAIL_PASSWORD: SecretStr | None = None

    # Пути
    STATIC_DIR: Path = BASE_DIR / "static"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"

    API_URL: str 
    VERIFICATION_TOKEN_EXPIRE_HOURS: int
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_proxies_list(self) -> list[str]:
        return [p.strip() for p in self.TRUSTED_PROXIES.split(",") if p.strip()]

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