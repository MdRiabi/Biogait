from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "BioGait API"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://biogait:biogaitsecret@db:5432/biogait"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "supersecretkeyforjwtsigningchangeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RATE_LIMIT: str = "100/minute"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()