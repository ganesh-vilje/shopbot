from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.customer import Customer
from app.models.order import Order, OrderItem

router = APIRouter(prefix="/api", tags=["orders"])


@router.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc())
    total = query.count()
    orders = query.options(joinedload(Order.items)).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total, "page": page, "limit": limit,
        "orders": [_order_dict(o) for o in orders],
    }


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
        Order.id == order_id, Order.customer_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_dict(order, detailed=True)


def _order_dict(o: Order, detailed: bool = False) -> dict:
    d = {
        "id": o.id, "order_number": o.order_number,
        "status": o.status.value, "subtotal": float(o.subtotal),
        "discount_amount": float(o.discount_amount),
        "tax_amount": float(o.tax_amount),
        "total_amount": float(o.total_amount),
        "payment_method": o.payment_method,
        "shipping_address": o.shipping_address,
        "tracking_number": o.tracking_number,
        "shipped_at": o.shipped_at.isoformat() if o.shipped_at else None,
        "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
        "created_at": o.created_at.isoformat(),
    }
    if detailed and o.items:
        d["items"] = [{
            "id": i.id, "product_id": i.product_id,
            "product_name": i.product.name if i.product else "",
            "quantity": i.quantity, "unit_price": float(i.unit_price),
            "discount_pct": float(i.discount_pct),
            "line_total": float(i.line_total),
        } for i in o.items]
    else:
        d["item_count"] = len(o.items) if o.items else 0
    return d
