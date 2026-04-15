import os
import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# FORCER LOCALHOST (pas 'db')
os.environ["DATABASE_URL"] = "postgresql+asyncpg://biogait:biogaitsecret@localhost:5432/biogait_test"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.db.session import get_db
from app.db.base import Base
from app.core.security import limiter
from app.api.v1.auth import router as auth_router
from app.api.v1.enrollment import router as enrollment_router

# CRÉER UNE APP FASTAPI MINIMALE SANS MIDDLEWARES PROBLÉMATIQUES
def create_test_app():
    app = FastAPI(title="BioGait Test")
    
    # Initialiser limiter AVANT tout
    app.state.limiter = limiter
    
    # UN SEUL middleware simple (CORS) - PAS de BaseHTTPMiddleware!
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Routes nécessaires
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(enrollment_router, prefix="/api/v1")
    
    return app

test_app = create_test_app()

# MOTEUR DE TEST ISOLÉ
from sqlalchemy.pool import NullPool
test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

test_app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac