import pytest
import base64
import numpy as np
import cv2
from starlette.testclient import TestClient
from app.main import app

def generate_black_frame_base64():
    """Génère une image 640x480 vide encodée en base64 pour simuler une caméra."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def test_websocket_stream():
    """
    Simule une caméra qui se connecte au websocket et envoie 30 frames
    pour vérifier que le RealtimeProcessor les reçoit, les floute et tente une IA.
    On utilise le TestClient sync standard de starlette pour tester les websockets.
    """
    client = TestClient(app)
    
    # On se connecte à la caméra "cam_front_door"
    with client.websocket_connect("/api/v1/recognition/ws/stream/cam_front_door") as websocket:
        # Envoie de 30 frames factices pour déclencher le process IA
        for _ in range(30):
            frame_str = generate_black_frame_base64()
            websocket.send_text(f"data:image/jpeg;base64,{frame_str}")
            
            # Réception du status ou decision
            data = websocket.receive_json()
            assert "status" in data
            
        assert data["status"] in ["processing", "decision_made"]
