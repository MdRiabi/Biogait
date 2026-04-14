import numpy as np
from typing import List, Tuple, Optional

# Indices des landmarks MediaPipe Pose sélectionnés (33 total, on utilise ces 18)
# NB : mediapipe n'est PAS importé ici — extractor.py reçoit des arrays numpy déjà extraits
SELECTED_LANDMARKS = [
    11, 12,  # Shoulders
    23, 24,  # Hips
    25, 26,  # Knees
    27, 28,  # Ankles
    29, 30,  # Heels
    31, 32,  # Feet indices (pivots)
    13, 14,  # Elbows
    15, 16,  # Wrists
    21, 22   # Foot thumbs (balance)
]

def normalize_keypoints(keypoints: np.ndarray, frame_shape: Tuple[int, int]) -> np.ndarray:
    """Normalise les keypoints en [0,1] relatif à la frame, centré sur le bassin."""
    h, w = frame_shape
    normalized = keypoints.copy()
    normalized[:, 0] /= w  # x normalisé
    normalized[:, 1] /= h  # y normalisé
    
    # Centrage sur le bassin moyen (landmarks 23,24)
    if len(keypoints) >= 24:
        hip_center = np.mean(keypoints[[23, 24], :2], axis=0)
        normalized[:, :2] -= hip_center / np.array([w, h])
    
    return normalized[:, :2]  # Retourne uniquement x,y

def compute_joint_angles(keypoints: np.ndarray) -> np.ndarray:
    """Calcule 12 angles articulaires principaux (en radians)."""
    angles = []
    
    def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
        v1_u = v1 / (np.linalg.norm(v1) + 1e-8)
        v2_u = v2 / (np.linalg.norm(v2) + 1e-8)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    
    # Angles jambes (genou, cheville)
    leg_pairs = [(24, 26, 28), (23, 25, 27)]  # Hip-Knee-Ankle L/R
    for hip, knee, ankle in leg_pairs:
        if knee < len(keypoints) and ankle < len(keypoints):
            v1 = keypoints[hip] - keypoints[knee]
            v2 = keypoints[ankle] - keypoints[knee]
            angles.append(angle_between(v1[:2], v2[:2]))
    
    # Angles bras (coude, poignet)
    arm_pairs = [(12, 14, 16), (11, 13, 15)]  # Shoulder-Elbow-Wrist L/R
    for shoulder, elbow, wrist in arm_pairs:
        if elbow < len(keypoints) and wrist < len(keypoints):
            v1 = keypoints[shoulder] - keypoints[elbow]
            v2 = keypoints[wrist] - keypoints[elbow]
            angles.append(angle_between(v1[:2], v2[:2]))
    
    # Oscillation latérale du bassin (différence hips x)
    if 23 < len(keypoints) and 24 < len(keypoints):
        angles.append(keypoints[24][0] - keypoints[23][0])
    
    # Inclinaison du torse (shoulders vs hips)
    if all(i < len(keypoints) for i in [11, 12, 23, 24]):
        shoulder_vec = keypoints[12] - keypoints[11]
        hip_vec = keypoints[24] - keypoints[23]
        angles.append(angle_between(shoulder_vec[:2], hip_vec[:2]))
    
    return np.array(angles + [0] * 12)[:12]  # Pad to 12

def compute_temporal_features(sequences: List[np.ndarray]) -> np.ndarray:
    """Calcule features temporelles sur une séquence de 30 frames."""
    if len(sequences) < 2:
        return np.zeros(16)
    
    features = []
    
    # Vitesse moyenne des keypoints (déplacement/frame)
    velocities = np.diff(sequences, axis=0)
    avg_velocity = np.mean(np.linalg.norm(velocities[:, :, :2], axis=2), axis=0)
    features.extend(avg_velocity[:8])  # 8 features
    
    # Rythme de marche (fréquence dominante via FFT simplifiée)
    hip_motion = np.array([seq[[23, 24], 1].mean() for seq in sequences])  # Y des hanches
    if len(hip_motion) >= 8:
        fft_vals = np.abs(np.fft.rfft(hip_motion - np.mean(hip_motion)))
        dominant_freq = np.argmax(fft_vals[1:]) + 1 if len(fft_vals) > 1 else 0
        features.append(dominant_freq / len(hip_motion))  # Normalized frequency
    else:
        features.append(0.0)
    
    # Longueur de foulée estimée (amplitude mouvement chevilles)
    if len(sequences) >= 10:
        ankle_range = np.ptp([seq[[27, 28], 0].mean() for seq in sequences])
        features.append(ankle_range)
    else:
        features.append(0.0)
    
    # Oscillation verticale du centre de masse
    com_y = np.array([seq[:, 1].mean() for seq in sequences])
    features.append(np.std(com_y))
    
    # Symétrie gauche/droite (corrélation mouvements jambes)
    if len(sequences) >= 5:
        left_leg = np.array([seq[25, 0] for seq in sequences])
        right_leg = np.array([seq[26, 0] for seq in sequences])
        if np.std(left_leg) > 1e-6 and np.std(right_leg) > 1e-6:
            corr = np.corrcoef(left_leg, right_leg)[0, 1]
            features.append(corr if not np.isnan(corr) else 0.0)
        else:
            features.append(0.0)
    else:
        features.append(0.0)
    
    return np.array(features + [0] * 16)[:16]  # Pad to 16

def extract_gait_vector(frames_keypoints: List[np.ndarray], frame_shapes: List[Tuple[int, int]]) -> np.ndarray:
    """
    Pipeline complet : keypoints bruts → vecteur biométrique 128D.
    
    Args:
        frames_keypoints: Liste de arrays [N_landmarks, 4] (x,y,visibilité,présence)
        frame_shapes: Liste de tuples (height, width) pour chaque frame
    
    Returns:
        np.ndarray de shape (128,) - vecteur normalisé L2
    """
    if not frames_keypoints or len(frames_keypoints) < 10:
        return np.zeros(128)
    
    # 1. Normalisation spatiale
    normalized = [
        normalize_keypoints(kp, shape) 
        for kp, shape in zip(frames_keypoints, frame_shapes)
    ]
    
    # 2. Features angulaires par frame (12 features × 30 frames = 360 → réduit à 40 par pooling)
    angle_features = np.array([compute_joint_angles(kp) for kp in normalized])
    angle_pooled = np.concatenate([
        np.mean(angle_features, axis=0),
        np.std(angle_features, axis=0),
        np.percentile(angle_features, [25, 75], axis=0).flatten()
    ])[:40]  # 12+12+16 = 40
    
    # 3. Features temporelles (16 features)
    temporal = compute_temporal_features(normalized)
    
    # 4. Features de posture moyenne (12 landmarks × 2 coords = 24 → 32 après padding)
    mean_pose = np.mean(np.array([kp[:, :2] for kp in normalized]), axis=0).flatten()
    mean_pose = np.pad(mean_pose, (0, max(0, 32 - len(mean_pose))), mode='constant')[:32]
    
    # 5. Concaténation + projection 128D via transformation linéaire simple
    raw_vector = np.concatenate([angle_pooled, temporal, mean_pose])  # 40+16+32 = 88
    extended = np.pad(raw_vector, (0, 128 - len(raw_vector)), mode='edge')[:128]
    
    # 6. Normalisation L2 pour compatibilité FAISS cosine/L2
    norm = np.linalg.norm(extended) + 1e-8
    return extended / norm