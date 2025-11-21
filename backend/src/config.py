"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_POOL_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str

    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: str
    STORAGE_CONTAINER_NAME: str = "artifacts"

    # Azure Service Bus
    SERVICE_BUS_CONNECTION_STRING: str

    # Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str
    JWT_AUDIENCE: str = "reportscheduler-api"

    # Email
    ACS_CONNECTION_STRING: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@reportscheduler.com"

    # Application
    ENVIRONMENT: str = "dev"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Observability
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""
    
    # Scheduler
    ENABLE_SCHEDULER: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development/local environment."""
        return self.ENVIRONMENT in ("dev", "local", "development")


# Global settings instance
settings = Settings()
