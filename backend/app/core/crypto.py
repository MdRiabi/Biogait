from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from app.config import get_settings

settings = get_settings()

import hashlib

def get_encryption_key() -> bytes:
    """Récupère ou génère une clé de chiffrement stable."""
    # En prod, charger depuis un secret manager ou vault
    # Pour le dev, on dérive de SECRET_KEY si pas de clé spécifique
    if hasattr(settings, 'AES_KEY') and settings.AES_KEY:
        return settings.AES_KEY.encode('utf-8')
    return hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()

def encrypt_vector(vector_bytes: bytes) -> tuple[bytes, bytes]:
    """Chiffre le vecteur biométrique et retourne (iv, ciphertext)."""
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce pour GCM
    ct = aesgcm.encrypt(nonce, vector_bytes, None)
    return nonce, ct

def decrypt_vector(nonce: bytes, ciphertext: bytes) -> bytes:
    """Déchiffre le vecteur biométrique."""
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ciphertext, None)
    return pt