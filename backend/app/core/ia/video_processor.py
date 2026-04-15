import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List
import mediapipe as mp
from app.core.ia.extractor import extract_gait_vector

class VideoProcessor:
    def __init__(self):
        self.mp_pose = mp.solutions.pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.5)

    def process_video_file(self, video_path: str) -> np.ndarray:
        """Extrait le vecteur gait d'un fichier vidéo."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")

        keypoints_seq = []
        frame_shapes = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_shape = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_pose.process(rgb_frame)
            
            if results.pose_landmarks:
                landmarks = []
                for lm in results.pose_landmarks.landmark:
                    landmarks.append([lm.x, lm.y, lm.visibility, 1.0])
                keypoints_seq.append(np.array(landmarks))
                frame_shapes.append(frame_shape)
        
        cap.release()
        self.mp_pose.close()

        if len(keypoints_seq) < 10:
            raise ValueError("Trop peu de frames détectées (min 10) pour l'enrôlement.")

        # Appel au pipeline d'extraction de l'Étape 2
        return extract_gait_vector(keypoints_seq, frame_shapes)