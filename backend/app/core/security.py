from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Optional
import secrets
import types

from jose import JWTError, jwt

try:
    import bcrypt as _bcrypt

    if hasattr(_bcrypt, "_bcrypt") and not hasattr(_bcrypt._bcrypt, "__about__"):
        _bcrypt._bcrypt.__about__ = types.SimpleNamespace(
            __version__=getattr(_bcrypt, "__version__", "unknown")
        )
except Exception:
    pass

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
