import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(100), index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)

    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
