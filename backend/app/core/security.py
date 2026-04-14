from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)