from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["auth"], redirect_slashes=False)

ACCESS_COOKIE_NAME = "shopbot_access_token"
REFRESH_COOKIE_NAME = "shopbot_refresh_token"


def _cookie_options(max_age: int) -> dict:
    options = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
        "max_age": max_age,
    }
    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN
    return options


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        **_cookie_options(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        **_cookie_options(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600),
    )


def _clear_auth_cookies(response: Response) -> None:
    delete_options = {"path": "/"}
    if settings.COOKIE_DOMAIN:
        delete_options["domain"] = settings.COOKIE_DOMAIN

    response.delete_cookie(ACCESS_COOKIE_NAME, **delete_options)
    response.delete_cookie(REFRESH_COOKIE_NAME, **delete_options)


def _make_session(user: Customer) -> tuple[str, str, UserResponse]:
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return access_token, refresh_token, UserResponse.model_validate(user)


@router.post("/signup", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.query(Customer).filter(
        func.lower(Customer.email) == email,
        Customer.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = Customer(
        full_name=payload.full_name,
        email=email,
        hashed_password=hash_password(payload.password),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token, refresh_token, user_response = _make_session(user)
    _set_auth_cookies(response, access_token, refresh_token)
    return {"user": user_response}


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(Customer).filter(
        func.lower(Customer.email) == email,
        Customer.deleted_at.is_(None),
    ).first()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token, refresh_token, user_response = _make_session(user)
    _set_auth_cookies(response, access_token, refresh_token)
    return {"user": user_response}


@router.post("/refresh", response_model=AuthSessionResponse)
def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    refresh_token_value = (
        (payload.refresh_token if payload else None)
        or (request.cookies.get(REFRESH_COOKIE_NAME) if request else None)
    )
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    refresh_payload = decode_refresh_token(refresh_token_value)
    if not refresh_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user_id = refresh_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    user = db.query(Customer).filter(Customer.id == user_id, Customer.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token, refresh_token, user_response = _make_session(user)
    if response is not None:
        _set_auth_cookies(response, access_token, refresh_token)
    return {"user": user_response}


@router.post("/logout")
def logout(response: Response):
    if response is not None:
        _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
