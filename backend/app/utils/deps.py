from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.db import get_db
from app.models.user import User
from app.utils.security import decode_token


# In-memory DB (moved here for now)
# db = {
#     "tim@example.com": {
#         "email": "tim@example.com",
#         "full_name": "Tim Goat",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False
#     }
# }
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  #this is to run the dummy endpoint

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
