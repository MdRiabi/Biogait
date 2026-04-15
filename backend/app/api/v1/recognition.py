import base64
import cv2
import numpy as np
import asyncio
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ia.realtime_processor import realtime_manager

router = APIRouter(prefix="/recognition", tags=["Recognition"])

class DashboardConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_alert(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

dashboard_manager = DashboardConnectionManager()

@router.websocket("/ws/stream/{camera_id}")
async def websocket_stream_endpoint(websocket: WebSocket, camera_id: str):
    """
    Endpoint recevant les frames vidéo encodées en Base64 JPEG.
    Le flux est analysé à la volée.
    """
    await websocket.accept()
    print(f"[{camera_id}] Connexion streaming acceptée.")
    
    try:
        while True:
            # Réception du payload text (JSON ou Base64 brut)
            data = await websocket.receive_text()
            
            # Si le client envoie JSON de type {"image": "base64..."} ou Base64 en brut, on gère.
            # Dans notre page de test, on enverra un data_url préfixé par 'data:image/jpeg;base64,'
            if data.startswith('data:image'):
                base64_data = data.split(',')[1]
            else:
                base64_data = data
                
            img_bytes = base64.b64decode(base64_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Traitement dans l'IA temps réel
                info = realtime_manager.process_frame(camera_id, frame)
                
                # S'il y a eu une décision
                if info.get("recognition"):
                    rec = info["recognition"]
                    # Push immédiat au dashboard
                    alert_msg = {
                        "camera_id": camera_id,
                        "timestamp": int(asyncio.get_event_loop().time()),
                        "recognition_result": rec
                    }
                    asyncio.create_task(dashboard_manager.broadcast_alert(alert_msg))
                    
                    # On en informe la caméra/client en retour
                    await websocket.send_json({"status": "decision_made", "result": rec})
                else:
                    # Accusé de réception basique (optionnel, sert à visualiser le flux)
                    await websocket.send_json({"status": "processing"})
                    
    except WebSocketDisconnect:
        print(f"[{camera_id}] Déconnexion streaming.")

@router.websocket("/ws/dashboard/alerts")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Connexion pour les clients Dashboard voulant voir les alertes en direct.
    """
    await dashboard_manager.connect(websocket)
    try:
        while True:
            # Maintien de connexion (Ping/Pong)
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)
