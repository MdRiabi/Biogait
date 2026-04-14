# backend/tests/conftest.py
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# 1️⃣ FORCER LOCALHOST AVANT TOUT IMPORT
os.environ["DATABASE_URL"] = "postgresql+asyncpg://biogait:biogaitsecret@localhost:5432/biogait"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.security import limiter

# 2️⃣ PATCH CRITIQUE : app.state.limiter DOIT exister avant les tests
app.state.limiter = limiter

# 3️⃣ RADICAL : Supprimer les middlewares BaseHTTPMiddleware qui cassent l'event loop sous Windows
# On garde uniquement CORS. SlowAPI et AuditMiddleware sont désactivés EN MODE TEST.
app.user_middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

# 4️⃣ MOTEUR DE TEST ISOLÉ
TEST_DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(TEST_DB_URL, echo=False, pool_size=5, max_overflow=10)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

app.dependency_overrides[get_db] = override_get_db

# 5️⃣ FIXTURES ASYNC PROPREMENT SCOPÉES
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac