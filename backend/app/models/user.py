# backend/app/models/user.py
from sqlalchemy import Column, String, Integer, DateTime, func, Enum, LargeBinary, Boolean
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
    
    # 🆕 Stockage biométrique chiffré (Étape 3)
    gait_iv = Column(LargeBinary, nullable=True)           # Nonce pour déchiffrement AES-GCM
    gait_template = Column(LargeBinary, nullable=True)     # Vecteur 128D chiffré
    is_enrolled = Column(Boolean, default=False)           # Flag d'état d'enrôlement
    is_approved = Column(Boolean, default=False)           # Approbation Admin requis