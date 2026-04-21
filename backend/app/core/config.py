from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Sentineloops API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
