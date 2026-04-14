import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.models.user import User, UserRole

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_register_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/register", json={"username": "testadmin", "password": "strongpass", "role": "admin"})
        assert res.status_code == 201
        
        res_login = await ac.post("/api/v1/auth/login", params={"username": "testadmin", "password": "strongpass"})
        assert res_login.status_code == 200
        assert "access_token" in res_login.json()

@pytest.mark.asyncio
async def test_rbac_restriction():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/v1/auth/register", json={"username": "viewer1", "password": "pass123", "role": "viewer"})
        res_login = await ac.post("/api/v1/auth/login", params={"username": "viewer1", "password": "pass123"})
        token = res_login.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        # Simuler un endpoint protégé (à implémenter dans étapes suivantes)
        # Pour l'étape 1, on vérifie juste que le token est valide via /me
        res_me = await ac.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["role"] == "viewer"