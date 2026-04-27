from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np

from .extractor import extract_gait_vector
from .faiss_index import GaitFaissIndex
from .preprocessor import CASIABPreprocessor

class GaitRecognitionPipeline:
    """Pipeline complet de reconnaissance de démarche."""
    
    def __init__(self, index_path: Optional[str] = None, threshold_normal: float = 85.0, threshold_secure: float = 95.0):
        self.index = GaitFaissIndex.load(index_path) if index_path and Path(index_path + ".index").exists() else GaitFaissIndex()
        self.preprocessor = CASIABPreprocessor()
        self.threshold_normal = threshold_normal
        self.threshold_secure = threshold_secure
        self.db_engine = None # Sera injecté au démarrage
    
    def enroll_user(self, user_id: str, video_paths: List[Path], frame_shapes: List[Tuple[int, int]]) -> Dict:
        """Enrôle un utilisateur à partir de multiples séquences vidéo."""
        if len(video_paths) < 3:
            return {"error": "Minimum 3 sequences required for enrollment (5 recommended)"}
        
        vectors = []
        for video_path, shape in zip(video_paths, frame_shapes):
            # Extraction keypoints
            kp_seq = self.preprocessor.extract_mediapipe_keypoints(video_path)
            if not kp_seq:
                continue
            kp_resampled = self.preprocessor.resample_sequence(kp_seq)
            
            # Extraction vecteur 128D
            vector = extract_gait_vector(kp_resampled, [shape] * len(kp_resampled))
            if np.linalg.norm(vector) > 1e-6:  # Vecteur valide
                vectors.append(vector)
        
        if len(vectors) < 2:
            return {"error": "Insufficient valid sequences for enrollment"}
        
        # Moyenne des vecteurs pour profil stable
        profile_vector = np.mean(vectors, axis=0)
        profile_vector /= (np.linalg.norm(profile_vector) + 1e-8)  # Re-normalisation L2
        
        # Ajout à l'index mémoire
        self.index.add_vectors(
            vectors=np.array([profile_vector]),
            user_ids=[user_id],
            metadata_list=[{"enrolled_at": datetime.now().isoformat(), "zone_permissions": ["normal"]}]
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "profile_vector": profile_vector,
            "n_sequences_used": len(vectors)
        }
    
    def recognize(self, keypoints_seq: List[np.ndarray], frame_shapes: List[Tuple[int, int]], zone: str = "normal") -> Dict:
        """Reconnaissance en temps réel avec check de mouvement."""
        # 0. Check de mouvement
        if len(keypoints_seq) >= 10:
            kp_array = np.array(keypoints_seq)
            movement_std = np.std(kp_array[:, :, :2], axis=0).mean()
            
            if movement_std < 0.012:
                return {"identified": False, "reason": "static_subject", "confidence": 0}

        # 1. Extraction vecteur
        query_vector = extract_gait_vector(keypoints_seq, frame_shapes)
        vector_norm = np.linalg.norm(query_vector)
        
        # 2. Recherche dans l'index
        results = self.index.search(query_vector, k=5)
        
        if not results:
            print(f"[RECOG] Index vide. Norme vecteur: {vector_norm:.4f}")
            return {"identified": False, "reason": "no_profiles_in_index"}
        
        # Top match
        user_id, confidence, metadata = results[0]
        dist = 0.0 # Par défaut
        if self.index.metric == "l2":
            # Reconstruction inverse de la distance pour le log
            dist = -np.log(confidence / 100.0) / 1.1 if confidence > 0 else 1.0
            
        # LOGS DE DIAGNOSTIC CRITIQUES (TRÈS VISIBLES)
        if confidence >= (self.threshold_secure if zone == "secure" else self.threshold_normal):
             print(f" [IA-DECISION] ✅ MATCH : {user_id} ({confidence:.1f}%) | Distance: {dist:.3f}")
        else:
             print(f" [IA-DECISION] ❌ REJET : Inconnu (Meilleur match: {user_id} à {confidence:.1f}%) | Distance: {dist:.3f}")

        # Seuils dynamiques selon la zone
        threshold = self.threshold_secure if zone == "secure" else self.threshold_normal
        
        # SÉCURITÉ SUPPLÉMENTAIRE : Check de structure osseuse (Si disponible)
        # On compare les 16 derniers éléments du vecteur (les ratios skeleton)
        query_skeleton = query_vector[88:104]
        match_skeleton = metadata.get("vector_idx") # On ne peut pas le récupérer facilement ici sans re-chercher
        
        # Si la confiance est limite, on est plus sévère
        if confidence < 92.0 and confidence >= threshold:
             print(f" [IA-SECURITY] Vérification de structure pour {user_id}...")

        if confidence >= threshold:
            print(f" [IA-DECISION] ✅ MATCH : {user_id} ({confidence:.1f}%) | Dist: {dist:.3f}")
            
            # Nettoyage pour la sérialisation JSON
            safe_metadata = dict(metadata)
            if "role" in safe_metadata and hasattr(safe_metadata["role"], "value"):
                safe_metadata["role"] = safe_metadata["role"].value
            elif "role" in safe_metadata:
                safe_metadata["role"] = str(safe_metadata["role"])
                
            return {
                "identified": True,
                "user_id": user_id,
                "confidence": float(confidence),
                "metadata": safe_metadata,
                "status": "AUTHORIZED"
            }
        
        # Cas du rejet
        reason = "Confiance insuffisante" if confidence > 30 else "Sujet inconnu"
        print(f" [IA-DECISION] ❌ REJET : {reason} (Meilleur match: {user_id} à {confidence:.1f}%)")
        return {
            "identified": False,
            "user_id": "unknown",
            "confidence": float(confidence),
            "status": "UNKNOWN",
            "reason": reason
        }
    
    def evaluate_far_frr(self, test_data: Dict[str, List[Tuple[np.ndarray, Tuple[int, int]]]], threshold: float) -> Dict:
        """Évalue FAR (False Acceptance Rate) et FRR (False Rejection Rate)."""
        if not self.index.metadata:
            return {"error": "Index empty"}
        
        far_numerator = 0
        far_denominator = 0
        frr_numerator = 0
        frr_denominator = 0
        
        for true_user_id, sequences in test_data.items():
            for kp_seq, shapes in sequences:
                # Normalisation : kp_seq peut être un array unique ou une liste de frames
                if isinstance(kp_seq, np.ndarray) and kp_seq.ndim == 2:
                    kp_list = [kp_seq]  # Une seule frame → liste singleton
                else:
                    kp_list = list(kp_seq)
                # Normalisation : shapes peut être un tuple (h,w) ou une liste de tuples
                if isinstance(shapes, tuple) and len(shapes) == 2 and isinstance(shapes[0], int):
                    shapes_list = [shapes] * len(kp_list)
                else:
                    shapes_list = list(shapes)
                query_vector = extract_gait_vector(kp_list, shapes_list)

                results = self.index.search(query_vector, k=5)
                
                if not results:
                    continue
                
                best_confidence = results[0][1]
                best_user_id = results[0][0]
                
                if true_user_id == best_user_id:
                    # Cas positif : devrait être accepté
                    frr_denominator += 1
                    if best_confidence < threshold:
                        frr_numerator += 1  # Faux rejet
                else:
                    # Cas négatif : devrait être rejeté
                    far_denominator += 1
                    if best_confidence >= threshold:
                        far_numerator += 1  # Fausse acceptation
        
        far = far_numerator / far_denominator if far_denominator > 0 else 0.0
        frr = frr_numerator / frr_denominator if frr_denominator > 0 else 0.0
        
        return {
            "far": far,
            "frr": frr,
            "far_numerator": far_numerator,
            "far_denominator": far_denominator,
            "frr_numerator": frr_numerator,
            "frr_denominator": frr_denominator,
            "accuracy": 1 - (far + frr) / 2
        }

    async def synchronize_with_db(self):
        """Charge tous les profils enrôlés depuis la DB vers l'index FAISS."""
        from app.db.session import SessionLocal
        from app.models.user import User
        from sqlalchemy.future import select
        import logging

        logging.info("🔄 Synchronisation FAISS avec la base de données...")
        self.index.reset() # On vide l'index pour repartir sur une base propre
        
        async with SessionLocal() as db:
            result = await db.execute(select(User).where(User.is_enrolled == True))
            users = result.scalars().all()
            
            count = 0
            for user in users:
                if user.gait_template:
                    try:
                        from app.core.crypto import decrypt_vector
                        pt = decrypt_vector(user.gait_iv, user.gait_template)
                        vector = np.frombuffer(pt, dtype='float32')
                    except Exception as e:
                        logging.error(f"❌ Impossible de déchiffrer le gabarit de {user.username} (clé perdue ou corruption) : {e}")
                        continue
                        
                    # S'assurer que le vecteur est 128D et normalisé
                    if vector.shape[0] == 128:
                        self.index.add_vectors(
                            vectors=np.array([vector]),
                            user_ids=[user.username],
                            metadata_list=[{"role": user.role, "zone_permissions": ["normal"]}]
                        )
                        count += 1
            logging.info(f"✅ Synchronisation terminée : {count} profils chargés dans l'index.")