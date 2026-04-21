import numpy as np
import cv2
from pathlib import Path
from typing import List, Tuple, Optional
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import RunningMode

# Chemin vers le modèle MediaPipe téléchargeable
# https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
_MODEL_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "pose_landmarker_lite.task"


class CASIABPreprocessor:
    """Adapte le dataset CASIA-B au format MediaPipe 17 keypoints (nouvelle API Tasks)."""

    # Mapping CASIA-B landmarks → MediaPipe indices (approximation)
    CASIA_TO_MP = {
        0: 11,   # Left shoulder
        1: 12,   # Right shoulder
        2: 13,   # Left elbow
        3: 14,   # Right elbow
        4: 15,   # Left wrist
        5: 16,   # Right wrist
        6: 23,   # Left hip
        7: 24,   # Right hip
        8: 25,   # Left knee
        9: 26,   # Right knee
        10: 27,  # Left ankle
        11: 28,  # Right ankle
        12: 29,  # Left heel
        13: 30,  # Right heel
    }

    def __init__(self, target_fps: int = 30, sequence_length: int = 30, model_path: Optional[Path] = None):
        self.target_fps = target_fps
        self.sequence_length = sequence_length
        self._model_path = model_path or _MODEL_PATH
        self._landmarker = None  # Initialisation lazy

    def _get_landmarker(self):
        """Initialise le PoseLandmarker à la demande (lazy init)."""
        if self._landmarker is None:
            if not self._model_path.exists():
                raise FileNotFoundError(
                    f"Modèle MediaPipe introuvable : {self._model_path}\n"
                    "Téléchargez-le avec :\n"
                    "  curl -L https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task "
                    f"-o {self._model_path}"
                )
            
            # --- FIX FOR WINDOWS ACCENTS (e.g., 'Biométrie') ---
            import tempfile
            import shutil
            import os
            temp_dir = tempfile.gettempdir()
            safe_model_path = os.path.join(temp_dir, "pose_landmarker_lite_temp.task")
            
            # Copie si nécessaire pour éviter les erreurs de lecture C++ de MediaPipe sur les chemins accentués
            if not os.path.exists(safe_model_path) or os.path.getmtime(safe_model_path) < self._model_path.stat().st_mtime:
                shutil.copy2(str(self._model_path), safe_model_path)
            
            base_options = mp_python.BaseOptions(model_asset_path=safe_model_path)
            options = mp_vision.PoseLandmarkerOptions(
                base_options=base_options,
                running_mode=RunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        return self._landmarker

    def extract_keypoints_from_frame(self, frame: np.ndarray, timestamp_ms: int) -> Optional[np.ndarray]:
        """Extrait les keypoints d'une frame unique (utile pour streaming)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        landmarker = self._get_landmarker()
        try:
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            # Si le timestamp n'est pas strictement croissant, on recrée le landmarker
            print(f"MediaPipe error: {e}, resetting landmarker...")
            self._landmarker = None
            landmarker = self._get_landmarker()
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            
        if result.pose_landmarks:
            landmarks = []
            for lm in result.pose_landmarks[0]:
                landmarks.append([lm.x, lm.y, lm.visibility, lm.presence])
            return np.array(landmarks)
        return None

    def extract_mediapipe_keypoints(self, video_path: Path) -> List[np.ndarray]:
        """Extrait les keypoints MediaPipe d'une vidéo CASIA-B."""
        # --- RESET LANDMARKER POUR CHAQUE VIDÉO (Évite l'erreur de timestamp) ---
        self._landmarker = None
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        landmarker = self._get_landmarker()
        keypoints_seq = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Conversion BGR → RGB pour MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Timestamp en millisecondes
            timestamp_ms = int(frame_idx * 1000 / fps)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                landmarks = []
                for lm in result.pose_landmarks[0]:
                    landmarks.append([lm.x, lm.y, lm.visibility, lm.presence])
                keypoints_seq.append(np.array(landmarks))

            frame_idx += 1

        cap.release()
        return keypoints_seq

    def resample_sequence(self, keypoints: List[np.ndarray]) -> List[np.ndarray]:
        """Resample la séquence à target_fps et sequence_length frames."""
        if len(keypoints) == 0:
            return []

        if len(keypoints) < self.sequence_length:
            # Upsample par interpolation linéaire
            indices = np.linspace(0, len(keypoints) - 1, self.sequence_length)
            resampled = []
            for idx in indices:
                i_low = int(np.floor(idx))
                i_high = min(int(np.ceil(idx)), len(keypoints) - 1)
                weight = idx - i_low
                interpolated = keypoints[i_low] * (1 - weight) + keypoints[i_high] * weight
                resampled.append(interpolated)
            return resampled
        elif len(keypoints) > self.sequence_length:
            # Downsample
            indices = np.linspace(0, len(keypoints) - 1, self.sequence_length).astype(int)
            return [keypoints[i] for i in indices]

        return keypoints

    def process_subject(self, subject_dir: Path) -> List[Tuple[np.ndarray, Tuple[int, int]]]:
        """Traite toutes les séquences d'un sujet CASIA-B."""
        sequences = []

        for video_file in subject_dir.glob("*.avi"):
            kp_seq = self.extract_mediapipe_keypoints(video_file)
            if not kp_seq:
                continue

            kp_resampled = self.resample_sequence(kp_seq)
            if not kp_resampled:
                continue

            cap = cv2.VideoCapture(str(video_file))
            ret, frame = cap.read()
            frame_shape = (frame.shape[0], frame.shape[1]) if ret else (480, 640)
            cap.release()

            sequences.append((np.array(kp_resampled), frame_shape))

        return sequences