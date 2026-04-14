import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.ia.extractor import extract_gait_vector, normalize_keypoints, compute_joint_angles
from app.core.ia.faiss_index import GaitFaissIndex
from app.core.ia.pipeline import GaitRecognitionPipeline

@pytest.fixture
def dummy_keypoints():
    """Génère des keypoints synthétiques pour tests."""
    np.random.seed(42)
    # 30 frames × 33 landmarks × 4 features (x,y,vis,presence)
    return [np.random.randn(33, 4) * 0.1 + np.array([0.5, 0.5, 1.0, 1.0]) for _ in range(30)]

@pytest.fixture
def dummy_frame_shapes():
    return [(480, 640)] * 30

def test_normalize_keypoints(dummy_keypoints):
    """Test la normalisation spatiale des keypoints."""
    kp = dummy_keypoints[0]
    normalized = normalize_keypoints(kp, (480, 640))
    
    assert normalized.shape == (33, 2)
    # Les valeurs devraient être centrées autour de 0 après normalisation
    assert -1.0 < normalized[:, 0].mean() < 1.0
    assert -1.0 < normalized[:, 1].mean() < 1.0

def test_compute_joint_angles(dummy_keypoints):
    """Test le calcul des angles articulaires."""
    kp = dummy_keypoints[0]
    angles = compute_joint_angles(kp)
    
    assert angles.shape == (12,)
    # Les angles en radians doivent être dans [0, pi] pour les angles réels
    assert np.all(angles[:10] >= 0) and np.all(angles[:10] <= np.pi)

def test_extract_gait_vector(dummy_keypoints, dummy_frame_shapes):
    """Test l'extraction complète du vecteur 128D."""
    vector = extract_gait_vector(dummy_keypoints, dummy_frame_shapes)
    
    assert vector.shape == (128,)
    # Normalisation L2 → norme ≈ 1
    assert 0.99 < np.linalg.norm(vector) < 1.01

def test_faiss_index_add_and_search():
    """Test l'index FAISS : ajout et recherche."""
    index = GaitFaissIndex(dimension=128)
    
    # Ajout de vecteurs synthétiques
    vectors = np.random.randn(10, 128).astype('float32')
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  # L2 norm
    
    index.add_vectors(
        vectors=vectors,
        user_ids=[f"user_{i}" for i in range(10)],
        metadata_list=[{"zone": "normal"}] * 10
    )
    
    assert index.index.ntotal == 10
    
    # Recherche avec un vecteur proche du premier
    query = vectors[0] + np.random.randn(128) * 0.01
    query = query / np.linalg.norm(query)
    
    results = index.search(query, k=3)
    
    assert len(results) >= 1
    # Le premier résultat devrait être user_0 avec haute confiance
    assert results[0][0] == "user_0"
    assert results[0][1] > 90  # >90% de confiance

def test_pipeline_enroll_and_recognize():
    """Test le pipeline complet : enrôlement + reconnaissance."""
    pipeline = GaitRecognitionPipeline()
    
    # Données synthétiques pour enrôlement
    video_paths = [Path(f"fake_{i}.mp4") for i in range(5)]
    frame_shapes = [(480, 640)] * 5
    
    with patch('app.core.ia.preprocessor.CASIABPreprocessor.extract_mediapipe_keypoints') as mock_extract:
        mock_extract.return_value = [np.random.randn(33, 4) * 0.1 + 0.5 for _ in range(30)]
        
        result = pipeline.enroll_user("test_user", video_paths, frame_shapes)
        
        assert result["success"] is True
        assert result["user_id"] == "test_user"
    
    # Test reconnaissance avec vecteur similaire
    test_kp = [np.random.randn(33, 4) * 0.1 + 0.5 for _ in range(30)]
    recognition = pipeline.recognize(test_kp, frame_shapes, zone="normal")
    
    # Devrait identifier test_user avec confiance > threshold_normal (75%)
    assert recognition["identified"] is True
    assert recognition["user_id"] == "test_user"
    assert recognition["confidence"] >= 75.0

def test_evaluate_far_frr():
    """Test l'évaluation FAR/FRR sur données synthétiques."""
    pipeline = GaitRecognitionPipeline()
    
    # Enrôlement de 2 utilisateurs
    for uid in ["user_a", "user_b"]:
        vectors = np.random.randn(3, 128).astype('float32')
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        pipeline.index.add_vectors(
            vectors=vectors,
            user_ids=[uid] * 3,
            metadata_list=[{"zone": "normal"}] * 3
        )
    
    # Données de test : séquences proches des profils enrôlés
    test_data = {
        "user_a": [(np.random.randn(33, 4) * 0.1 + 0.5, (480, 640)) for _ in range(5)],
        "user_b": [(np.random.randn(33, 4) * 0.1 + 0.5, (480, 640)) for _ in range(5)]
    }
    
    metrics = pipeline.evaluate_far_frr(test_data, threshold=75.0)
    
    # Sur données synthétiques, on s'attend à des métriques raisonnables
    assert 0 <= metrics["far"] <= 1
    assert 0 <= metrics["frr"] <= 1
    # Accuracy devrait être > 0.5 sur ce toy dataset
    assert metrics["accuracy"] >= 0.5