from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api import auth, chat, users, products, orders
from app.db.session import engine
from app.models.refresh_session import RefreshSession

app = FastAPI(
    title="ShopBot API",
    redirect_slashes=False,
    description="AI-powered e-commerce chat assistant backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

# Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.on_event("startup")
def ensure_auth_tables() -> None:
    # Keep the dedicated auth session table available even if a local database
    # has not yet applied the latest migration.
    RefreshSession.__table__.create(bind=engine, checkfirst=True)


@app.get("/health")
def health():
    return {"status": "ok", "company": settings.COMPANY_NAME}
