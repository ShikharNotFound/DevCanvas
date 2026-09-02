from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.auth import UserCreate, UserLogin, Token, User          # Pydantic schema
from app.models.user import User as UserModel                             # SQLAlchemy model
from app.utils.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.utils.deps import get_current_active_user, oauth2_scheme
from app.db import get_db

router = APIRouter()

@router.post("/register", response_model=Token, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    user = UserModel(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token({"sub": user.email}),
        "refresh_token": create_refresh_token({"sub": user.email}),
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return {
        "access_token": create_access_token({"sub": user.email}),
        "refresh_token": create_refresh_token({"sub": user.email}),
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload.get("sub")
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "access_token": create_access_token({"sub": user.email}),
        "refresh_token": create_refresh_token({"sub": user.email}),
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    # Return the Pydantic User schema, not the SQLAlchemy model
    return User(
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active
    )