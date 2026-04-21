from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.ia.realtime_processor import realtime_manager
from app.core.ia.anonymizer import VideoAnonymizer
from app.models.alert import DetectionAlert
from app.db.session import SessionLocal
import json
import logging
import base64
import cv2
import numpy as np
import asyncio
from typing import List
from app.core.state import latest_frames

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

@router.websocket("/ws/mobile")
async def websocket_mobile_endpoint(websocket: WebSocket):
    """Endpoint spécifique pour recevoir les frames via JSON de la caméra mobile."""
    await websocket.accept()
    print("[Mobile] Connexion caméra nomade acceptée.")
    try:
        while True:
            import json
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            camera_id = data.get("camera_id", "mobile_cam")
            image_data = data.get("image")
            
            if image_data and image_data.startswith('data:image'):
                base64_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # 1. Anonymisation (RGPD)
                    anonymizer = VideoAnonymizer()
                    frame = anonymizer.blur_faces(frame)
                    
                    # 2. Conversion en Base64 après floutage pour l'affichage dashboard
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    anonymized_b64 = base64.b64encode(buffer).decode()
                    
                    # 3. Traitement IA (Reconnaissance réelle)
                    info = realtime_manager.process_frame(camera_id, frame)
                    
                    if info.get("processed"):
                         print(f"[ENGINE] Image reçue pour {camera_id} - IA Active")

                    if info.get("recognition"):
                        rec = info["recognition"]
                        alert_msg = {
                            "type": "alert",
                            "camera_id": camera_id,
                            "timestamp": int(asyncio.get_event_loop().time()),
                            "recognition_result": rec
                        }
                        # Sauvegarde en base de données
                        async with SessionLocal() as db:
                            new_alert = DetectionAlert(
                                camera_id=camera_id,
                                identified=rec.get("identified", False),
                                username=rec.get("user_id"),
                                confidence=rec.get("confidence", 0.0) / 100.0,
                                anonymized_image=anonymized_b64
                            )
                            db.add(new_alert)
                            await db.commit()
                            
                        asyncio.create_task(dashboard_manager.broadcast_alert(alert_msg))
                    
                    # 4. Diffusion de l'image ANONYMISÉE au dashboard
                    latest_frames[camera_id] = f"data:image/jpeg;base64,{anonymized_b64}"
                    
                    frame_msg = {
                        "type": "frame",
                        "camera_id": camera_id,
                        "image": latest_frames[camera_id]
                    }
                    asyncio.create_task(dashboard_manager.broadcast_alert(frame_msg))
    except WebSocketDisconnect:
        print("[Mobile] Déconnexion caméra nomade.")

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
