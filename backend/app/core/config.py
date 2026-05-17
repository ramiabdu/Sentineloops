from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "SentinelOps API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+psycopg://sentinelops:sentinelops@localhost:5432/sentinelops"
    DATABASE_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    AUTH_SECRET_KEY: str = "sentinelops-local-dev-secret"
    AUTH_TOKEN_TTL_MINUTES: int = 60
    AUTH_DEMO_EMAIL: str = "analyst@sentinelops.local"
    AUTH_DEMO_DISPLAY_NAME: str = "SentinelOps Analyst"
    AUTH_DEMO_ROLE: str = "admin"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
