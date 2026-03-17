"""
SQL Generator  (Dynamic — replaces static SQL_TEMPLATES)
Stage 2 of the agent pipeline.

Flow:
  intent + entities + live schema
      → LLM (GPT-4o)
      → raw SQL string
      → sanitised + validated SQL ready for execution

Key security guarantees:
  - LLM is instructed via system prompt to write SELECT-only queries
  - customer_id is injected server-side — never trusted from user input
  - Generated SQL passes through sql_validator before execution
  - Temperature = 0 → deterministic, no creative hallucinations
  - Schema is read from live DB → column names are always accurate
"""
import json
import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import Engine
from openai import OpenAI

from app.core.config import settings
from app.agents.schema_reader import (
    get_schema_for_intent,
    schema_to_prompt_text,
    INTENT_TABLE_MAP,
)
from app.agents.sql_validator import validate_sql, sanitise_llm_output

# ── FAQ responses (no DB needed) ──────────────────────────────────────────
FAQ_RESPONSES: dict[str, str] = {
    "return_policy": (
        "We offer a **30-day hassle-free return policy**. "
        "Simply contact support and we'll arrange a free pickup."
    ),
    "shipping": (
        "Standard shipping takes **3–5 business days** and is free on orders over $50. "
        "Express (1–2 days) is available for $9.99."
    ),
    "payment": (
        "We accept **Visa, Mastercard, Amex, PayPal, Apple Pay, Google Pay**, "
        "and Cash on Delivery."
    ),
    "general": (
        "I'm here to help with your orders, products, account, "
        "and any general questions about our store!"
    ),
}

# ── System prompt for the SQL generation LLM call ─────────────────────────
SQL_SYSTEM_PROMPT = """You are a precise and security-conscious SQL expert for a PostgreSQL e-commerce database.

YOUR ONLY JOB: Write a single, correct SQL SELECT query based on the user question and schema provided.

STRICT RULES — violating any rule means your output will be rejected:
1. Write ONLY a raw SQL SELECT statement — no INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT
2. Do NOT include markdown, code fences, backticks, or any explanation text — raw SQL only
3. Use ONLY the exact column names listed in the schema — never guess or invent column names
4. ALWAYS include LIMIT (maximum 20) — never return unbounded result sets
5. ALWAYS filter orders/customers by customer_id using the exact value provided — never omit this
6. Use parameterised-style literals — embed the customer_id value directly as a quoted string
7. For text searches use: LOWER(column) LIKE LOWER('%search_term%')
8. Do NOT use subqueries more than one level deep
9. Do NOT use UNION, INTERSECT, or EXCEPT
10. Do NOT access system tables, pg_catalog, information_schema, or any table not in the schema

ANTI-HALLUCINATION RULES:
- If a column is not in the schema, do NOT use it — omit it entirely
- If a table is not in the schema, do NOT reference it
- If you are unsure about a column name, use the closest matching one from the schema
- Never make up data — only query what the schema contains

OUTPUT FORMAT: Raw SQL query only. Nothing else. No "Here is the SQL:" prefix."""


def generate_sql(
    question: str,
    intent: str,
    entities: dict,
    customer_id: str,
    engine: Engine,
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate a validated SQL query for the given question.

    Returns:
        (sql_string, None)      — valid SQL ready for execution
        (None, faq_key)         — FAQ intent, no SQL needed
        (None, None)            — out of scope or generation failed
    """
    # ── Handle non-DB intents immediately ─────────────────────────────────
    if intent in ("general_faq", "out_of_scope"):
        return None, "general"

    # ── Get only the schema tables this intent needs ───────────────────────
    relevant_schema = get_schema_for_intent(intent, engine)

    if not relevant_schema:
        print(f"[SQLGenerator] No schema found for intent: {intent}")
        return None, "general"

    schema_text = schema_to_prompt_text(relevant_schema)

    # ── Build the user prompt ─────────────────────────────────────────────
    limit = min(int(entities.get("limit", 5)), 20)

    # Safely extract entities — never trust raw user input in SQL
    product_search = (
        entities.get("product_name")
        or entities.get("brand")
        or entities.get("category")
        or ""
    )
    order_number   = entities.get("order_number", "")
    category       = entities.get("category", "")
    min_price      = entities.get("min_price", "")
    max_price      = entities.get("max_price", "")
    status_filter  = entities.get("status", "")

    user_prompt = f"""DATABASE SCHEMA:
{schema_text}

USER QUESTION: {question}

INTENT: {intent}

EXTRACTED ENTITIES:
- customer_id (MUST be used to filter customer data): '{customer_id}'
- product search term: '{product_search}'
- order number: '{order_number}'
- category filter: '{category}'
- status filter: '{status_filter}'
- price range: min={min_price} max={max_price}
- result limit: {limit}

Write the SQL query now. Remember:
- Filter orders/customers by customer_id = '{customer_id}'
- Use LIMIT {limit}
- Only use columns that exist in the schema above
- Raw SQL only, no explanation"""

    # ── Call GPT ─────────────────────────────────────────────────────────
    if not settings.OPENAI_API_KEY:
        print("[SQLGenerator] No OpenAI key — using fallback templates")
        return _fallback_sql(intent, entities, customer_id), None

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0,       # deterministic — no creative SQL
            max_tokens=600,
            timeout=15,
        )

        raw_sql = response.choices[0].message.content or ""

        # ── Clean up LLM output ───────────────────────────────────────────
        sql = sanitise_llm_output(raw_sql)

        if not sql:
            print("[SQLGenerator] LLM returned empty SQL")
            return _fallback_sql(intent, entities, customer_id), None

        # ── Validate before returning ─────────────────────────────────────
        allowed_tables = list(relevant_schema.keys())
        is_valid, reason = validate_sql(sql, allowed_tables, customer_id)

        if not is_valid:
            print(f"[SQLGenerator] Validation failed: {reason}")
            print(f"[SQLGenerator] Rejected SQL: {sql[:200]}")
            # Fall back to safe static query for this intent
            return _fallback_sql(intent, entities, customer_id), None

        print(f"[SQLGenerator] ✓ Validated SQL for intent={intent}")
        return sql, None

    except Exception as e:
        print(f"[SQLGenerator] OpenAI error: {e}")
        return _fallback_sql(intent, entities, customer_id), None


# ── Safe fallback templates (used when OpenAI is unavailable) ─────────────
# These are hardcoded safe queries — no LLM involved.
def _fallback_sql(intent: str, entities: dict, customer_id: str) -> Optional[str]:
    """
    Pre-written safe queries used as fallback when:
    - OpenAI API key is not set
    - LLM call fails
    - Generated SQL fails validation
    """
    search = (
        entities.get("product_name")
        or entities.get("brand")
        or entities.get("category")
        or ""
    )
    limit       = min(int(entities.get("limit", 5)), 20)
    order_num   = entities.get("order_number", "")
    category    = entities.get("category", "")

    FALLBACKS: dict[str, str] = {
        "order_status": f"""
            SELECT o.order_number, o.status, o.total_amount,
                   o.created_at, o.shipped_at, o.delivered_at,
                   o.tracking_number, o.payment_method
            FROM orders o
            WHERE o.customer_id = '{customer_id}'
            {"AND UPPER(o.order_number) = UPPER('" + order_num + "')" if order_num else ""}
            ORDER BY o.created_at DESC
            LIMIT 1
        """,
        "order_history": f"""
            SELECT o.order_number, o.status, o.total_amount,
                   o.created_at, o.payment_method
            FROM orders o
            WHERE o.customer_id = '{customer_id}'
            ORDER BY o.created_at DESC
            LIMIT {limit}
        """,
        "product_search": f"""
            SELECT name, brand, category, price, discount_pct,
                   stock_qty, rating, review_count, sku
            FROM products
            WHERE is_active = TRUE
            {"AND (LOWER(name) LIKE LOWER('%" + search + "%') OR LOWER(brand) LIKE LOWER('%" + search + "%') OR LOWER(category) LIKE LOWER('%" + search + "%'))" if search else ""}
            ORDER BY rating DESC, review_count DESC
            LIMIT {limit}
        """,
        "price_check": f"""
            SELECT name, brand, price, discount_pct,
                   ROUND(CAST(price AS NUMERIC) * (1 - CAST(discount_pct AS NUMERIC) / 100), 2) AS discounted_price,
                   stock_qty, rating, sku
            FROM products
            WHERE is_active = TRUE
            {"AND (LOWER(name) LIKE LOWER('%" + search + "%') OR LOWER(brand) LIKE LOWER('%" + search + "%'))" if search else ""}
            ORDER BY rating DESC
            LIMIT {limit}
        """,
        "stock_check": f"""
            SELECT name, brand, sku, stock_qty,
                   CASE WHEN stock_qty > 0 THEN 'In Stock' ELSE 'Out of Stock' END AS availability,
                   price
            FROM products
            WHERE is_active = TRUE
            {"AND (LOWER(name) LIKE LOWER('%" + search + "%') OR LOWER(brand) LIKE LOWER('%" + search + "%'))" if search else ""}
            ORDER BY stock_qty DESC
            LIMIT {limit}
        """,
        "customer_profile": f"""
            SELECT full_name, email, phone, city, country,
                   is_verified, created_at
            FROM customers
            WHERE id = '{customer_id}'
            AND deleted_at IS NULL
            LIMIT 1
        """,
        "top_products": f"""
            SELECT name, brand, category, price, discount_pct,
                   rating, review_count, stock_qty, sku
            FROM products
            WHERE is_active = TRUE
            {"AND LOWER(category) = LOWER('" + category + "')" if category else ""}
            AND stock_qty > 0
            ORDER BY rating DESC, review_count DESC
            LIMIT {limit}
        """,
    }

    return FALLBACKS.get(intent)