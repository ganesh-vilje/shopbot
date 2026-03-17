"""
Schema Reader
Reads all table names, column names, types and relationships
directly from the live PostgreSQL database using SQLAlchemy inspect.
Never goes stale — always reflects the real DB state.
Results are cached in memory at startup and refreshed on demand.
"""
import json
from functools import lru_cache
from sqlalchemy import inspect, Engine
from sqlalchemy.orm import Session

# Tables that should NEVER be exposed to the LLM
# (internal/auth tables — no customer should query these)
BLOCKED_TABLES = {
    "alembic_version",
    "conversations",
    "messages",
}

# Only these tables are allowed for customer-facing queries
ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_items",
}

# Intent → which tables are relevant (keeps LLM prompt small and focused)
INTENT_TABLE_MAP: dict[str, list[str]] = {
    "order_status"    : ["orders", "customers"],
    "order_history"   : ["orders", "order_items", "products"],
    "product_search"  : ["products"],
    "price_check"     : ["products"],
    "stock_check"     : ["products"],
    "customer_profile": ["customers"],
    "top_products"    : ["products"],
    "general_faq"     : [],
    "out_of_scope"    : [],
}


def read_full_schema(engine: Engine) -> dict[str, list[dict]]:
    """
    Read all tables and their columns from the live database.
    Returns a dict: { table_name: [ {name, type, nullable, primary_key} ] }
    Only returns ALLOWED_TABLES — never exposes internal tables.
    """
    inspector = inspect(engine)
    schema: dict[str, list[dict]] = {}

    all_tables = inspector.get_table_names()

    for table in all_tables:
        # Only expose allowed business tables
        if table not in ALLOWED_TABLES:
            continue

        columns = inspector.get_columns(table)
        pk_cols = {col for col in inspector.get_pk_constraint(table).get("constrained_columns", [])}
        fk_list = inspector.get_foreign_keys(table)

        # Build FK lookup: column_name → referenced_table.column
        fk_map: dict[str, str] = {}
        for fk in fk_list:
            for col in fk.get("constrained_columns", []):
                ref_table = fk.get("referred_table", "")
                ref_cols  = fk.get("referred_columns", [])
                if ref_table and ref_cols:
                    fk_map[col] = f"{ref_table}.{ref_cols[0]}"

        schema[table] = [
            {
                "name"       : col["name"],
                "type"       : str(col["type"]),
                "nullable"   : col["nullable"],
                "primary_key": col["name"] in pk_cols,
                "foreign_key": fk_map.get(col["name"]),  # e.g. "customers.id"
            }
            for col in columns
        ]

    return schema


def get_schema_for_intent(
    intent: str,
    engine: Engine,
) -> dict[str, list[dict]]:
    """
    Return only the schema sections relevant to the given intent.
    This keeps LLM prompts small and prevents the model from
    hallucinating columns from unrelated tables.
    """
    relevant_tables = INTENT_TABLE_MAP.get(intent, [])

    if not relevant_tables:
        return {}

    full_schema = read_full_schema(engine)

    return {
        table: full_schema[table]
        for table in relevant_tables
        if table in full_schema
    }


def schema_to_prompt_text(schema: dict[str, list[dict]]) -> str:
    """
    Convert schema dict into a clean, readable text block
    that LLMs understand well. Includes column types and FK references.

    Example output:
        TABLE: orders
          - id              VARCHAR   (primary key)
          - customer_id     VARCHAR   → customers.id
          - order_number    VARCHAR
          - status          VARCHAR
          - total_amount    NUMERIC(12, 2)
    """
    if not schema:
        return "No tables available."

    lines = []
    for table, columns in schema.items():
        lines.append(f"TABLE: {table}")
        for col in columns:
            parts = [f"  - {col['name']:<20} {col['type']}"]
            if col.get("primary_key"):
                parts.append("(primary key)")
            if col.get("foreign_key"):
                parts.append(f"→ {col['foreign_key']}")
            if not col.get("nullable") and not col.get("primary_key"):
                parts.append("[NOT NULL]")
            lines.append(" ".join(parts))
        lines.append("")  # blank line between tables

    return "\n".join(lines)