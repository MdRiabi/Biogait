import pytest
from sqlalchemy import select
from app.models.user import User

@pytest.mark.asyncio
async def test_register_and_login(client):
    # Inscription
    res = await client.post("/api/v1/auth/register", json={
        "username": "testadmin",
        "password": "strongpass",
        "role": "admin"
    })
    assert res.status_code == 201

    # Connexion
    res_login = await client.post("/api/v1/auth/login", params={
        "username": "testadmin",
        "password": "strongpass"
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

@pytest.mark.asyncio
async def test_rbac_restriction(client):
    # Création viewer
    await client.post("/api/v1/auth/register", json={
        "username": "viewer1",
        "password": "pass123",
        "role": "viewer"
    })
    
    # Login viewer
    res_login = await client.post("/api/v1/auth/login", params={
        "username": "viewer1",
        "password": "pass123"
    })
    token = res_login.json()["access_token"]
    
    # Vérification profil
    res_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "viewer"