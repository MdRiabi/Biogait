from sqlalchemy import Column, String, Integer, DateTime, func
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(20), nullable=False) # method
    resource = Column(String(255), nullable=False) # path
    ip_address = Column(String(45))
    status_code = Column(Integer)
    details = Column(String(500))