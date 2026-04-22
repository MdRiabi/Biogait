from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    APP_NAME: str = "BioGait API"
    DEBUG: bool = False
    # App sur la machine hôte → localhost. Dans Docker (même compose), utiliser @db:5432
    DATABASE_URL: str = "postgresql+asyncpg://biogait:biogaitsecret@127.0.0.1:5432/biogait"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "supersecretkeyforjwtsigningchangeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RATE_LIMIT: str = "100/minute"

@lru_cache
def get_settings():
    return Settings()