from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api import auth, chat, users, products, orders

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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok", "company": settings.COMPANY_NAME}
