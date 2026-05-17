from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "SentinelOps API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+psycopg://sentinelops:sentinelops@localhost:5432/sentinelops"
    DATABASE_ECHO: bool = False
    AUTH_SECRET_KEY: str = "sentinelops-local-dev-secret"
    AUTH_TOKEN_TTL_MINUTES: int = 60
    AUTH_DEMO_EMAIL: str = "analyst@sentinelops.local"
    AUTH_DEMO_DISPLAY_NAME: str = "SentinelOps Analyst"
    AUTH_DEMO_ROLE: str = "admin"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


settings = Settings()
