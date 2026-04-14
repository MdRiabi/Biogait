import pytest
import numpy as np
import time
from app.core.ia.faiss_index import GaitFaissIndex

def test_faiss_benchmark():
    """Benchmark réaliste : 1000 vecteurs, 100 requêtes."""
    index = GaitFaissIndex(dimension=128)
    
    # Simulation de 1000 profils utilisateurs
    n_users = 1000
    vectors = np.random.randn(n_users, 128).astype('float32')
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    
    index.add_vectors(
        vectors=vectors,
        user_ids=[f"user_{i:04d}" for i in range(n_users)],
        metadata_list=[{"zone": "normal"}] * n_users
    )
    
    # Benchmark
    benchmark = index.benchmark_search(n_queries=100)
    
    # Vérification des contraintes de performance
    assert benchmark["latency_p95_ms"] < 50, f"P95 latency {benchmark['latency_p95_ms']:.2f}ms > 50ms target"
    assert benchmark["throughput_qps"] > 20, f"Throughput {benchmark['throughput_qps']:.1f} QPS < 20 target"
    
    print(f"✅ Benchmark OK: P95={benchmark['latency_p95_ms']:.2f}ms, QPS={benchmark['throughput_qps']:.1f}")