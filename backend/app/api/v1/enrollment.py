from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.core.ia.video_processor import VideoProcessor
from app.core.crypto import encrypt_vector
import os
import tempfile
import numpy as np

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])

@router.post("/register", status_code=201)
async def enroll_new_user(
    username: str,
    video_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Vérification existence utilisateur
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 2. Sauvegarde temporaire et traitement IA
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            content = await video_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        processor = VideoProcessor()
        vector = processor.process_video_file(tmp_path)
        
        # 3. Validation du vecteur (doit être 128D)
        if vector.shape != (128,):
            raise ValueError("Extraction de vecteur échouée ou format incorrect.")

        # 4. Chiffrement du vecteur
        vector_bytes = vector.astype('float32').tobytes()
        nonce, ciphertext = encrypt_vector(vector_bytes)

        # 5. Création utilisateur avec gabarit biométrique
        new_user = User(
            username=username,
            hashed_password="dummy_hash_for_enroll", # À remplacer par vrai mot de passe
            gait_iv=nonce,
            gait_template=ciphertext,
            is_enrolled=True
        )
        db.add(new_user)
        await db.commit()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Nettoyage fichier temp
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"msg": f"Utilisateur {username} enrôlé avec succès."}

@router.get("/check/{username}")
async def check_enrollment(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "is_enrolled": user.is_enrolled}