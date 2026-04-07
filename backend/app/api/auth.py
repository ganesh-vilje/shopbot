from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.customer import Customer
from app.models.refresh_session import RefreshSession
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
ACCESS_COOKIE_PATH = "/"
REFRESH_COOKIE_PATH = "/auth"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cookie_options(max_age: int, path: str) -> dict:
    options = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": path,
        "max_age": max_age,
    }
    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN
    return options


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        **_cookie_options(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, ACCESS_COOKIE_PATH),
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        **_cookie_options(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600, REFRESH_COOKIE_PATH),
    )


def _delete_cookie(response: Response, cookie_name: str, path: str) -> None:
    delete_options = {"path": path}
    if settings.COOKIE_DOMAIN:
        delete_options["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(cookie_name, **delete_options)


def _clear_auth_cookies(response: Response) -> None:
    _delete_cookie(response, ACCESS_COOKIE_NAME, ACCESS_COOKIE_PATH)
    _delete_cookie(response, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH)
    _delete_cookie(response, REFRESH_COOKIE_NAME, ACCESS_COOKIE_PATH)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else None


def _create_refresh_session(
    db: Session,
    user: Customer,
    request: Request | None,
    *,
    family_id: str | None = None,
    parent_session_id: str | None = None,
) -> tuple[str, RefreshSession]:
    refresh_token = generate_refresh_token()
    refresh_session = RefreshSession(
        customer_id=user.id,
        token_hash=hash_token(refresh_token),
        family_id=family_id or str(uuid.uuid4()),
        parent_session_id=parent_session_id,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=_client_ip(request),
        last_used_at=_utcnow(),
        expires_at=_utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_session)
    db.flush()
    return refresh_token, refresh_session


def _make_session(
    db: Session,
    user: Customer,
    request: Request | None,
    response: Response,
    *,
    family_id: str | None = None,
    parent_session_id: str | None = None,
) -> UserResponse:
    refresh_token, refresh_session = _create_refresh_session(
        db,
        user,
        request,
        family_id=family_id,
        parent_session_id=parent_session_id,
    )
    access_token = create_access_token(
        data={"sub": user.id, "sid": refresh_session.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.commit()
    _set_auth_cookies(response, access_token, refresh_token)
    return UserResponse.model_validate(user)


def _revoke_session(
    session: RefreshSession,
    *,
    reason: str,
    replaced_by_session_id: str | None = None,
) -> None:
    session.revoked_at = _utcnow()
    session.revoke_reason = reason
    session.replaced_by_session_id = replaced_by_session_id
    session.last_used_at = _utcnow()


def _revoke_family(db: Session, family_id: str, reason: str) -> None:
    now = _utcnow()
    active_sessions = db.query(RefreshSession).filter(
        RefreshSession.family_id == family_id,
        RefreshSession.revoked_at.is_(None),
    ).all()
    for session in active_sessions:
        session.revoked_at = now
        session.revoke_reason = reason
        session.last_used_at = now


def _find_refresh_session(db: Session, refresh_token: str) -> RefreshSession | None:
    return db.query(RefreshSession).filter(
        RefreshSession.token_hash == hash_token(refresh_token),
    ).first()


@router.post("/signup", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
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
    db.flush()
    user_response = _make_session(db, user, request, response)
    return {"user": user_response}


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()
    user = db.query(Customer).filter(
        func.lower(Customer.email) == email,
        Customer.deleted_at.is_(None),
    ).first()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_response = _make_session(db, user, request, response)
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
        or request.cookies.get(REFRESH_COOKIE_NAME)
    )
    if not refresh_token_value:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Missing refresh token")

    session = _find_refresh_session(db, refresh_token_value)
    if not session:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if session.revoked_at is not None:
        _revoke_family(db, session.family_id, "refresh_token_reuse_detected")
        db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    if session.expires_at <= _utcnow():
        _revoke_session(session, reason="refresh_token_expired")
        db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(Customer).filter(
        Customer.id == session.customer_id,
        Customer.deleted_at.is_(None),
    ).first()
    if not user:
        _revoke_session(session, reason="user_not_found")
        db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="User not found")

    session.last_used_at = _utcnow()
    replacement_refresh_token, replacement_session = _create_refresh_session(
        db,
        user,
        request,
        family_id=session.family_id,
        parent_session_id=session.id,
    )
    _revoke_session(
        session,
        reason="rotated",
        replaced_by_session_id=replacement_session.id,
    )

    access_token = create_access_token(
        data={"sub": user.id, "sid": replacement_session.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.commit()

    _set_auth_cookies(response, access_token, replacement_refresh_token)
    return {"user": UserResponse.model_validate(user)}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    revoked = False
    refresh_token_value = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token_value:
        session = _find_refresh_session(db, refresh_token_value)
        if session and session.revoked_at is None:
            _revoke_session(session, reason="logout")
            revoked = True

    access_token_value = request.cookies.get(ACCESS_COOKIE_NAME)
    if access_token_value:
        payload = decode_access_token(access_token_value)
        session_id = payload.get("sid") if payload else None
        if session_id:
            session = db.query(RefreshSession).filter(RefreshSession.id == session_id).first()
            if session and session.revoked_at is None:
                _revoke_session(session, reason="logout")
                revoked = True

    if revoked:
        db.commit()

    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
