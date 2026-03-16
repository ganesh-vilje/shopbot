from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
)
from app.core.redis_client import get_redis
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse,
    UserResponse, RefreshRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


def _make_token_response(user: Customer) -> dict:
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token()
    redis = get_redis()
    redis.setex(f"refresh:{refresh_token}", REFRESH_TTL, user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter(Customer.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = Customer(
        full_name=payload.full_name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        is_verified=True,   # skip email verification for simplicity
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _make_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limit: max 10 attempts per IP per 15 min
    ip = request.client.host if request.client else "unknown"
    redis = get_redis()
    key = f"login_attempts:{ip}"
    attempts = redis.incr(key)
    if attempts == 1:
        redis.expire(key, 900)
    if attempts > 10:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 15 minutes.")

    user = db.query(Customer).filter(
        Customer.email == payload.email.lower(),
        Customer.deleted_at.is_(None),
    ).first()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    redis.delete(key)  # reset on success
    return _make_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    redis = get_redis()
    user_id = redis.get(f"refresh:{payload.refresh_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(Customer).filter(Customer.id == user_id, Customer.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    redis.delete(f"refresh:{payload.refresh_token}")
    return _make_token_response(user)


@router.post("/logout")
def logout(payload: RefreshRequest):
    redis = get_redis()
    redis.delete(f"refresh:{payload.refresh_token}")
    return {"message": "Logged out successfully"}
