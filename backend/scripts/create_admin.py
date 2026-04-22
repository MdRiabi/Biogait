import asyncio
import sys
import os

# Ajout du chemin pour importer 'app'
sys.path.append(os.getcwd())

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

async def create_admin():
    print("--- Création du compte Administrateur BioGait ---")
    
    # 1. Initialisation des tables (si SQLITE vide)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with SessionLocal() as db:
        # 2. Vérification si déjà un admin
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        if result.scalar_one_or_none():
            print("❌ Un administrateur existe déjà dans la base.")
            return

        # 3. Création du compte
        username = input("Nom d'utilisateur admin (défaut: mohamed) : ") or "mohamed"
        password = input("Mot de passe admin (défaut: admin123) : ") or "admin123"
        
        admin_user = User(
            username=username,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_approved=True, # L'admin est auto-approuvé
            is_enrolled=False
        )
        
        db.add(admin_user)
        try:
            await db.commit()
            print(f"✅ Compte ADMIN créé avec succès !")
            print(f"   Utilisateur : {username}")
            print(f"   Mot de passe : {password}")
            print("\nVous pouvez maintenant vous connecter au Dashboard.")
        except Exception as e:
            await db.rollback()
            print(f"❌ Erreur lors de la création : {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_admin())
