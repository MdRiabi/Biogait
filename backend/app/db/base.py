from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Importation des modèles après Base pour éviter les cycles
try:
    from app.models.user import User
    from app.models.audit import AuditLog
    from app.models.alert import DetectionAlert
except ImportError:
    pass
