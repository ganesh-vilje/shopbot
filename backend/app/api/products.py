from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.api.deps import get_current_user, get_db
from app.models.customer import Customer
from app.models.product import Product

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
def list_products(
    q: str = Query(None),
    category: str = Query(None),
    brand: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    in_stock: bool = Query(None),
    sort: str = Query("rating"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active == True)
    if q:
        query = query.filter(or_(
            func.lower(Product.name).contains(q.lower()),
            func.lower(Product.brand).contains(q.lower()),
            func.lower(Product.category).contains(q.lower()),
        ))
    if category:
        query = query.filter(func.lower(Product.category) == category.lower())
    if brand:
        query = query.filter(func.lower(Product.brand) == brand.lower())
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock:
        query = query.filter(Product.stock_qty > 0)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.rating.desc(), Product.review_count.desc())

    total = query.count()
    products = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total, "page": page, "limit": limit,
        "products": [_product_dict(p) for p in products],
    }


@router.get("/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_dict(p)


def _product_dict(p: Product) -> dict:
    return {
        "id": p.id, "sku": p.sku, "name": p.name,
        "description": p.description, "category": p.category,
        "brand": p.brand, "price": float(p.price),
        "discount_pct": float(p.discount_pct),
        "discounted_price": round(float(p.price) * (1 - float(p.discount_pct) / 100), 2),
        "stock_qty": p.stock_qty, "image_url": p.image_url,
        "rating": float(p.rating), "review_count": p.review_count,
        "is_active": p.is_active,
    }
