from sqlalchemy import Column, String, Integer, DateTime, func, Enum
import enum
from app.db.base import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    created_at = Column(DateTime, server_default=func.now())