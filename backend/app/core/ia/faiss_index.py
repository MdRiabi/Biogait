import faiss
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import json
import time

class GaitFaissIndex:
    """Index FAISS optimisé pour la recherche de vecteurs de démarche 128D."""
    
    def __init__(self, dimension: int = 128, metric: str = "l2"):
        self.dimension = dimension
        self.metric = metric
        self.index = None
        self.metadata: dict = {}  # id → {user_id, enrolled_at, zone_permissions}
        self._init_index()
    
    def _init_index(self):
        """Initialise l'index FAISS avec métrique appropriée."""
        if self.metric == "l2":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.metric == "cosine":
            # FAISS n'a pas IndexFlatCosine natif → normalisation L2 + L2 = cosine
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            raise ValueError(f"Metric {self.metric} not supported")

    def reset(self):
        """Vide l'index et les métadonnées."""
        self._init_index()
        self.metadata = {}
    
    def add_vectors(self, vectors: np.ndarray, user_ids: List[str], metadata_list: List[dict]):
        """Ajoute des vecteurs à l'index avec métadonnées."""
        if len(vectors) != len(user_ids) or len(vectors) != len(metadata_list):
            raise ValueError("Length mismatch between vectors, user_ids, and metadata")
        
        # Conversion float32 requise par FAISS
        vectors_f32 = vectors.astype('float32')
        
        # Ajout à l'index
        start_idx = self.index.ntotal
        self.index.add(vectors_f32)
        
        # Stockage métadonnées
        for i, (uid, meta) in enumerate(zip(user_ids, metadata_list)):
            self.metadata[start_idx + i] = {
                "user_id": uid,
                **meta,
                "vector_idx": start_idx + i
            }
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, dict]]:
        """
        Recherche les k plus proches voisins.
        
        Returns:
            Liste de tuples (user_id, score_confiance [0-100], metadata)
        """
        if self.index.ntotal == 0:
            return []
        
        query_f32 = query_vector.astype('float32').reshape(1, -1)
        
        # Recherche
        distances, indices = self.index.search(query_f32, min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS retourne -1 pour les slots vides
                continue
            
            meta = self.metadata.get(int(idx), {})
            
            # Conversion distance → score de confiance [0-100]
            if self.metric == "l2":
                # L2 distance: 0 = identique, plus grand = plus différent
                # Normalisation heuristique: score = 100 * exp(-distance/2)
                confidence = 100.0 * np.exp(-dist / 2.0)
            else:  # cosine via L2-normalized
                # distance cosine ≈ 2(1-cos_sim) → cos_sim = 1 - dist/2
                cos_sim = 1.0 - dist / 2.0
                confidence = max(0, min(100, cos_sim * 100))
            
            results.append((meta.get("user_id", "unknown"), float(confidence), meta))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def benchmark_search(self, n_queries: int = 100) -> dict:
        """Benchmark de performance de recherche."""
        if self.index.ntotal < 10:
            return {"error": "Index too small for benchmark"}
        
        # Génération de requêtes aléatoires (distribution similaire aux données réelles)
        queries = np.random.randn(n_queries, self.dimension).astype('float32')
        # Normalisation L2 pour cohérence
        queries = queries / (np.linalg.norm(queries, axis=1, keepdims=True) + 1e-8)
        
        times = []
        for query in queries:
            start = time.perf_counter()
            self.search(query, k=5)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
        
        return {
            "n_vectors": self.index.ntotal,
            "n_queries": n_queries,
            "latency_p50_ms": np.percentile(times, 50),
            "latency_p95_ms": np.percentile(times, 95),
            "latency_p99_ms": np.percentile(times, 99),
            "throughput_qps": n_queries / (sum(times) / 1000)
        }
    
    def save(self, filepath: str):
        """Sauvegarde l'index et les métadonnées."""
        faiss.write_index(self.index, filepath + ".index")
        with open(filepath + ".meta.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str, dimension: int = 128, metric: str = "l2") -> "GaitFaissIndex":
        """Charge un index FAISS existant."""
        instance = cls(dimension=dimension, metric=metric)
        instance.index = faiss.read_index(filepath + ".index")
        with open(filepath + ".meta.json", "r") as f:
            instance.metadata = json.load(f)
        return instance