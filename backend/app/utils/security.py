import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt with automatic salt."""
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def get_password_hash(password: str) -> str:
    """Alias for hash_password – used in auth endpoints."""
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token (default 30 minutes)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token (default 7 days)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode a JWT and return its payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None