"""
Stage 2 — SQL Generator
Builds safe, parameterised SQL queries based on intent + entities.
"""
from typing import Any


SQL_TEMPLATES: dict[str, str] = {
    "order_status": """
        SELECT o.order_number, o.status, o.total_amount, o.created_at,
               o.shipped_at, o.delivered_at, o.tracking_number, o.payment_method,
               c.full_name AS customer_name
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.customer_id = :customer_id
          AND (:order_number IS NULL OR UPPER(o.order_number) = UPPER(:order_number))
        ORDER BY o.created_at DESC
        LIMIT 1
    """,
    "order_history": """
        SELECT o.order_number, o.status, o.total_amount, o.created_at,
               COUNT(oi.id) AS item_count
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.customer_id = :customer_id
        GROUP BY o.id, o.order_number, o.status, o.total_amount, o.created_at
        ORDER BY o.created_at DESC
        LIMIT :limit
    """,
    "product_search": """
        SELECT id, name, brand, category, price, discount_pct,
               stock_qty, rating, review_count, sku, image_url
        FROM products
        WHERE is_active = TRUE
          AND (:search IS NULL OR
               LOWER(name) LIKE LOWER('%' || :search || '%') OR
               LOWER(brand) LIKE LOWER('%' || :search || '%') OR
               LOWER(category) LIKE LOWER('%' || :search || '%') OR
               LOWER(description) LIKE LOWER('%' || :search || '%'))
        ORDER BY rating DESC, review_count DESC
        LIMIT :limit
    """,
    "price_check": """
        SELECT name, brand, price, discount_pct,
               ROUND(price * (1 - discount_pct / 100), 2) AS discounted_price,
               stock_qty, rating, sku
        FROM products
        WHERE is_active = TRUE
          AND (:search IS NULL OR
               LOWER(name) LIKE LOWER('%' || :search || '%') OR
               LOWER(brand) LIKE LOWER('%' || :search || '%'))
        ORDER BY rating DESC
        LIMIT :limit
    """,
    "stock_check": """
        SELECT name, brand, sku, stock_qty,
               CASE WHEN stock_qty > 0 THEN 'In Stock' ELSE 'Out of Stock' END AS availability,
               price
        FROM products
        WHERE is_active = TRUE
          AND (:search IS NULL OR
               LOWER(name) LIKE LOWER('%' || :search || '%') OR
               LOWER(brand) LIKE LOWER('%' || :search || '%'))
        ORDER BY stock_qty DESC
        LIMIT :limit
    """,
    "customer_profile": """
        SELECT full_name, email, phone, city, country,
               loyalty_points, is_verified, created_at
        FROM customers
        WHERE id = :customer_id AND deleted_at IS NULL
    """,
    "top_products": """
        SELECT name, brand, category, price, discount_pct, rating,
               review_count, stock_qty, image_url, sku
        FROM products
        WHERE is_active = TRUE
          AND (:category IS NULL OR LOWER(category) = LOWER(:category))
          AND stock_qty > 0
        ORDER BY rating DESC, review_count DESC
        LIMIT :limit
    """,
}

FAQ_RESPONSES = {
    "return_policy": "We offer a **30-day hassle-free return policy**. Simply contact support and we'll arrange a free pickup.",
    "shipping": "Standard shipping takes **3–5 business days** and is free on orders over $50. Express (1–2 days) is available for $9.99.",
    "payment": "We accept **Visa, Mastercard, Amex, PayPal, Apple Pay, Google Pay**, and Cash on Delivery.",
    "general": "I'm here to help with orders, products, your account, and general queries about our store!",
}


def generate_query(intent: str, entities: dict, customer_id: str) -> tuple[str | None, dict[str, Any], str | None]:
    """
    Returns (sql_template, params_dict, faq_key_or_None).
    Returns (None, {}, faq_key) for FAQ / out-of-scope intents.
    """
    search = (
        entities.get("product_name")
        or entities.get("brand")
        or entities.get("category")
    )
    limit = min(int(entities.get("limit", 5)), 20)

    if intent in SQL_TEMPLATES:
        params: dict[str, Any] = {
            "customer_id": customer_id,
            "search": search,
            "order_number": entities.get("order_number"),
            "category": entities.get("category"),
            "limit": limit,
        }
        return SQL_TEMPLATES[intent], params, None

    if intent == "general_faq":
        return None, {}, "general"

    return None, {}, "general"
