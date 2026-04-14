from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password
from app.core.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=dict, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(User).where(User.username == user.username))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Username already exists")
    new_user = User(username=user.username, hashed_password=hash_password(user.password), role=user.role)
    db.add(new_user)
    return {"msg": "User created"}

@router.post("/login", response_model=Token)
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role, "id": current_user.id}