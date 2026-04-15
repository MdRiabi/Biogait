from contextlib import asynccontextmanager
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
logging.basicConfig(level=logging.INFO)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database initialized & tables created.")
    yield
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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>BioGait API</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>Identification BioGait active ✅</h1>
            <p>L'API est en ligne. Accédez à la <a href="/docs">Documentation Swagger</a>.</p>
            <p>Pour tester la reconnaissance en direct : <a href="/test-cam">Lancer le test Webcam</a></p>
        </body>
    </html>
    """

@app.get("/test-cam")
async def test_cam():
    # Sert le fichier HTML de test situé dans tests/test_cam.html
    file_path = os.path.join(os.path.dirname(__file__), "..", "tests", "test_cam.html")
    return FileResponse(file_path)

@app.get("/health")
async def health():
    return {"status": "ok"}