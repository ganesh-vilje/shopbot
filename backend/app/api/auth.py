from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_refresh_token,
)
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import (
    SignupRequest, LoginRequest, AuthSessionResponse,
    UserResponse, RefreshRequest,
)
import httpx
from urllib.parse import urlencode


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
    access_token, refresh_token, user_response = _make_session(user)
    _set_auth_cookies(response, access_token, refresh_token)
    return {"user": user_response}


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(Customer).filter(
        Customer.email == payload.email.lower(),
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
def logout(
    response: Response,
):
    if response is not None:
        _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/oauth/google")
def oauth_google_redirect():
    """Redirect user to Google login page."""
    params = {
        "client_id"    : settings.GOOGLE_CLIENT_ID,
        "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope"        : "openid email profile",
        "access_type"  : "offline",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url)


@router.get("/oauth/callback")
def oauth_callback(code: str, db: Session = Depends(get_db)):
    """Google sends the user back here with a code."""
    # Exchange code for token
    token_res = httpx.post("https://oauth2.googleapis.com/token", data={
        "code"         : code,
        "client_id"    : settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri" : settings.GOOGLE_REDIRECT_URI,
        "grant_type"   : "authorization_code",
    })
    token_data = token_res.json()
    access_token_google = token_data.get("access_token")

    # Get user info from Google
    user_res  = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token_google}"}
    )
    user_info = user_res.json()

    email     = user_info.get("email")
    full_name = user_info.get("name", email)
    oauth_id  = user_info.get("id")

    # Upsert customer
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        customer = Customer(
            full_name      = full_name,
            email          = email,
            is_verified    = True,
            oauth_provider = "google",
            oauth_id       = oauth_id,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    from fastapi.responses import RedirectResponse
    access_token, refresh_token, _ = _make_session(customer)
    response = RedirectResponse(f"{settings.FRONTEND_URL}/oauth/success")
    _set_auth_cookies(response, access_token, refresh_token)
    return response


@router.get("/oauth/github")
def oauth_github_redirect():
    """Redirect user to GitHub login page."""
    from urllib.parse import urlencode
    from fastapi.responses import RedirectResponse

    params = {
        "client_id"   : settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope"       : "user:email",
    }
    url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/oauth/github/callback")
def oauth_github_callback(code: str, db: Session = Depends(get_db)):
    """GitHub sends the user back here with a code."""
    import httpx
    from fastapi.responses import RedirectResponse

    # Exchange code for access token
    token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id"    : settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code"         : code,
            "redirect_uri" : settings.GITHUB_REDIRECT_URI,
        }
    )
    token_data  = token_res.json()
    github_token = token_data.get("access_token")

    if not github_token:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/login?error=github_auth_failed"
        )

    # Get user info from GitHub
    user_res  = httpx.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept"       : "application/vnd.github+json",
        }
    )
    user_info = user_res.json()

    # GitHub may not return email publicly — fetch separately
    email = user_info.get("email")
    if not email:
        emails_res = httpx.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept"       : "application/vnd.github+json",
            }
        )
        emails = emails_res.json()
        # Pick the primary verified email
        for e in emails:
            if e.get("primary") and e.get("verified"):
                email = e.get("email")
                break

    if not email:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/login?error=no_email"
        )

    full_name = user_info.get("name") or user_info.get("login") or email
    oauth_id  = str(user_info.get("id"))

    # Upsert customer
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        customer = Customer(
            full_name      = full_name,
            email          = email,
            is_verified    = True,
            oauth_provider = "github",
            oauth_id       = oauth_id,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    access_token, refresh_token, _ = _make_session(customer)
    response = RedirectResponse(f"{settings.FRONTEND_URL}/oauth/success")
    _set_auth_cookies(response, access_token, refresh_token)
    return response
