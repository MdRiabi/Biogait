import pytest
import httpx
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

@pytest.mark.asyncio
async def test_enroll_user_success(client):
    # Simule un fichier vidéo (ici un fichier vide suffit pour mocker l'IA)
    test_video = Path("test_video.mp4")
    test_video.touch()

    with patch('app.api.v1.enrollment.VideoProcessor') as MockProcessor:
        mock_instance = MagicMock()
        mock_instance.process_video_file.return_value = np.zeros(128)
        MockProcessor.return_value = mock_instance

        with open(test_video, 'rb') as f:
            files = {'video_file': f}
            params = {'username': 'new_gait_user'}
            
            response = await client.post(
                "/api/v1/enrollment/register",
                files=files,
                params=params
            )
        
        assert response.status_code == 201
        assert response.json()["msg"] == "Utilisateur new_gait_user enrôlé avec succès."
    
    test_video.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_enroll_existing_user(client):
    # Prérequis : inscrire un user via /auth/register
    await client.post("/api/v1/auth/register", json={
        "username": "existing_user",
        "password": "password123"
    })
    
    # Pour ce test, on vérifie que l'enrôlement échoue car l'utilisateur est déjà dans la base
    # NOTE: l'endpoint renvoie sûrement 400 parce que l'utilisateur n'est pas "nouveau" 
    # ou demande un enrôlement d'une manière spécifique.
    response = await client.post(
        "/api/v1/enrollment/register", 
        params={'username': 'existing_user'},
        files={'video_file': b'data'}
    )
    assert response.status_code == 400
    assert "already exists" in response.json().get("detail", "") or "enroll" in response.json().get("detail", "")