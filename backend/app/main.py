from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
import os
from app.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.core.middleware import AuditMiddleware
from app.core.security import limiter
from app.api.v1.auth import router as auth_router

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
import logging
from app.api.v1.enrollment import router as enrollment_router
from app.api.v1.recognition import router as recognition_router
import sys
from nicegui import ui

# Ajout du dossier racine au path pour trouver le module 'frontend'
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.main import init_frontend
logging.basicConfig(level=logging.INFO)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialisation de la base de données (SQLite automatique)
    from app.db.base import Base
    from app.db.session import engine, SessionLocal
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database initialized (SQLite).")
    
    # 2. Bootstrap Admin (Création du premier compte si vide)
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    from sqlalchemy.future import select
    
    async with SessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            admin_user = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_approved=True
            )
            db.add(admin_user)
            await db.commit()
            logging.info("🚀 Default admin created (admin / admin123).")

    # 3. Synchronisation du moteur IA au démarrage
    from app.core.ia.realtime_processor import realtime_manager
    asyncio.create_task(realtime_manager.pipeline.synchronize_with_db())
    
    yield
    
    # Nettoyage
    await engine.dispose()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# 🔥 CRITIQUE : DOIT être défini IMMÉDIATEMENT après l'instanciation
app.state.limiter = limiter

# Ajout des middlewares APRÈS l'initialisation du state
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc):
    return {"detail": "Rate limit exceeded. Try again later."}

app.include_router(auth_router, prefix="/api/v1")
app.include_router(enrollment_router, prefix="/api/v1")
app.include_router(recognition_router, prefix="/api/v1")

# Initialisation du Dashboard NiceGUI (Étape 5)
init_frontend()

# Montage de NiceGUI sur FastAPI (Définit les routes / et /login par défaut)
ui.run_with(
    app,
    storage_secret="biogait_secret_session_key_123", # À changer en prod
    title="BioGait Admin Dashboard",
    dark=True
)

@app.get("/health")

@app.get("/test-cam")
async def test_cam():
    # Sert le fichier HTML de test situé dans tests/test_cam.html
    file_path = os.path.join(os.path.dirname(__file__), "..", "tests", "test_cam.html")
    return FileResponse(file_path)

@app.get("/health")
async def health():
    return {"status": "ok"}