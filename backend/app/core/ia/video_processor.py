import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List
from app.core.ia.preprocessor import CASIABPreprocessor
from app.core.ia.extractor import extract_gait_vector

class VideoProcessor:
    def __init__(self):
        # On utilise le préprocesseur moderne déjà existant dans le projet
        self.preprocessor = CASIABPreprocessor()

    def process_video_file(self, video_path: str) -> np.ndarray:
        """Extrait le vecteur gait d'un fichier vidéo en utilisant l'API Tasks."""
        # 1. Extraction des points clés via MediaPipe Tasks
        # (Cette méthode gère déjà l'ouverture de la vidéo et le landmarker)
        keypoints_seq = self.preprocessor.extract_mediapipe_keypoints(Path(video_path))
        
        if len(keypoints_seq) < 10:
            raise ValueError(f"Trop peu de frames détectées ({len(keypoints_seq)}) pour l'enrôlement.")

        # 2. On récupère les dimensions de la vidéo pour la normalisation
        cap = cv2.VideoCapture(video_path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        frame_shapes = [(h, w)] * len(keypoints_seq)

        # 3. Appel au pipeline d'extraction biométrique final
        return extract_gait_vector(keypoints_seq, frame_shapes)