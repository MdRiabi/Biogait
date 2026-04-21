from collections import deque
import numpy as np
import time
from typing import Dict, Deque, Tuple
import asyncio
from app.core.ia.pipeline import GaitRecognitionPipeline
from app.core.ia.anonymizer import VideoAnonymizer

class RealtimeGaitManager:
    """Gestionnaire de files d'attente pour la reconnaissance temps réel."""

    def __init__(self, pipeline: GaitRecognitionPipeline, sequence_length: int = 30):
        self.pipeline = pipeline
        self.sequence_length = sequence_length
        self.anonymizer = VideoAnonymizer()
        
        # Mapping camera_id -> deque (buffers)
        self.buffers: Dict[str, Deque[np.ndarray]] = {}
        # Mapping camera_id -> buffer des shapes associés (frames originaux)
        self.shape_buffers: Dict[str, Deque[Tuple[int, int]]] = {}
        # Mapping camera_id -> timestamp (dernier frame géré)
        self.timestamps: Dict[str, int] = {}
        
        # Mapping camera_id -> nombre de frames vides consécutives
        self.empty_counters: Dict[str, int] = {}
        
        # Zones définies pour caméra (valeur par défaut)
        self.camera_zones: Dict[str, str] = {
            "cam_front_door": "normal",
            "cam_server_room": "secure"
        }

    def process_frame(self, camera_id: str, frame: np.ndarray) -> Dict:
        """
        Processus exécuté pour CHAQUE frame reçu.
        1. Anonymisation (TTL en RAM)
        2. Extraction des keypoints
        3. Si personne n'est détecté -> Reset Buffer
        4. Si 30 frames se sont écoulées -> Reconnaissance IA + Purge Totale
        """
        if camera_id not in self.buffers:
            self.buffers[camera_id] = deque(maxlen=self.sequence_length)
            self.shape_buffers[camera_id] = deque(maxlen=self.sequence_length)
            self.timestamps[camera_id] = int(time.time() * 1000)
            self.empty_counters[camera_id] = 0

        # 1. Anonymisation
        frame_anon = self.anonymizer.blur_faces(frame)

        # 2. Extraction des keypoints
        now_ms = int(time.time() * 1000)
        self.timestamps[camera_id] = max(now_ms, self.timestamps[camera_id] + 1)

        frame_shape = (frame.shape[0], frame.shape[1])
        kp = self.pipeline.preprocessor.extract_keypoints_from_frame(frame_anon, self.timestamps[camera_id])
        
        # 3. Détecteur de disparition (Sécurité Critique)
        if kp is None:
            self.empty_counters[camera_id] += 1
            # Si vide pendant 3 frames (~0.3s), on vide tout pour éviter le mélange de sujets
            if self.empty_counters[camera_id] >= 3 and len(self.buffers[camera_id]) > 0:
                print(f"[SECURITY] Sujet disparu sur {camera_id}. Purge du buffer.")
                self.buffers[camera_id].clear()
                self.shape_buffers[camera_id].clear()
        else:
            self.empty_counters[camera_id] = 0
            self.buffers[camera_id].append(kp)
            self.shape_buffers[camera_id].append(frame_shape)

        result = None
        # 4. Reconnaissance IA
        if len(self.buffers[camera_id]) == self.sequence_length:
            zone = self.camera_zones.get(camera_id, "normal")
            kp_seq = self.pipeline.preprocessor.resample_sequence(list(self.buffers[camera_id]))
            shapes_list = list(self.shape_buffers[camera_id])
            
            try:
                rec_result = self.pipeline.recognize(kp_seq, shapes_list, zone=zone)
                result = rec_result
                
                # PURGE TOTALE APPRÈS RECONNAISSANCE (Zéro mélange)
                print(f"[SECURITY] Reconnaissance terminée pour {camera_id}. Purge totale du buffer.")
                self.buffers[camera_id].clear()
                self.shape_buffers[camera_id].clear()
            except Exception as e:
                print(f"Error in recognition: {e}")
                self.buffers[camera_id].clear()
                self.shape_buffers[camera_id].clear()

        # La frame est détruite automatiquement en quittant le scope (TTL 0)
        return {
            "processed": True,
            "face_blurred": True,
            "recognition": result
        }

# Instance globale (Singleton pour le prototype)
pipeline = GaitRecognitionPipeline()
realtime_manager = RealtimeGaitManager(pipeline)
