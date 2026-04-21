from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, func
from app.db.base import Base

class DetectionAlert(Base):
    __tablename__ = "detection_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    camera_id = Column(String(50), index=True)
    
    # Résultat IA
    identified = Column(Boolean, default=False)
    username = Column(String(100), nullable=True) # Nom de la personne identifiée
    confidence = Column(Float) # Score de confiance (0.0 - 1.0)
    
    # Métadonnées
    is_anomaly = Column(Boolean, default=False) # Si le comportement est suspect
    anonymized_image = Column(String, nullable=True) # Stockage Base64 de l'image floutée (optionnel)
    status = Column(String(20), default="NEW") # NEW, REVIEWED, ARCHIVED
