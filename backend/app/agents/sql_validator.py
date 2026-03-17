"""
SQL Validator
Multi-layer safety gate that sits between the LLM output
and the database. Every generated SQL must pass ALL checks
before execution. Rejects anything suspicious — better to
return no result than to run a dangerous query.
"""
import re
from typing import Optional

# ── Forbidden SQL keywords — block any mutation or schema changes ──────────
WRITE_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "UPSERT", "REPLACE",
    "DROP", "TRUNCATE", "ALTER", "CREATE", "RENAME",
    "GRANT", "REVOKE", "EXECUTE", "EXEC", "CALL",
    "COPY", "VACUUM", "ANALYZE", "REINDEX",
]

# ── Tables that must never appear in any generated query ──────────────────
FORBIDDEN_TABLES = [
    "alembic_version",
    "conversations",
    "messages",
]

# ── Patterns that indicate SQL injection attempts ─────────────────────────
INJECTION_PATTERNS = [
    r";\s*SELECT",          # stacked queries
    r";\s*DROP",
    r";\s*INSERT",
    r"--\s",                # inline comment (common in injections)
    r"/\*.*?\*/",           # block comment
    r"\bUNION\b.*\bSELECT\b",  # UNION-based injection
    r"\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",  # OR 1=1
    r"\bAND\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",  # AND 1=1
    r"xp_cmdshell",         # MSSQL specific but block anyway
    r"pg_sleep",            # time-based blind injection
    r"pg_read_file",
    r"lo_export",
    r"INFORMATION_SCHEMA",  # schema probing
    r"pg_catalog",
]

# ── Maximum allowed complexity ─────────────────────────────────────────────
MAX_SQL_LENGTH  = 2000   # characters
MAX_JOIN_COUNT  = 4      # number of JOIN clauses
MAX_SUBQUERIES  = 1      # number of nested SELECT


class SQLValidationError(Exception):
    """Raised when generated SQL fails a safety check."""
    pass


def validate_sql(
    sql: str,
    allowed_tables: list[str],
    customer_id: str,
) -> tuple[bool, str]:
    """
    Run all safety checks on the LLM-generated SQL.

    Returns:
        (True, "OK")              — safe to execute
        (False, "reason string")  — unsafe, do not execute

    Checks performed (in order):
        1. Not empty / not too long
        2. Starts with SELECT (read-only enforcement)
        3. No write / schema-change keywords
        4. No forbidden tables
        5. No SQL injection patterns
        6. Must have a LIMIT clause
        7. LIMIT value is reasonable (≤ 100)
        8. No more than MAX_JOIN_COUNT JOINs
        9. No more than MAX_SUBQUERIES nested SELECTs
        10. customer_id is present for customer-specific intents
    """
    if not sql or not sql.strip():
        return False, "Empty SQL generated"

    sql_clean   = sql.strip()
    sql_upper   = sql_clean.upper()
    sql_single  = " ".join(sql_clean.split())  # collapse whitespace

    # ── 1. Length guard ────────────────────────────────────────────────────
    if len(sql_clean) > MAX_SQL_LENGTH:
        return False, f"SQL too long ({len(sql_clean)} chars). Possible injection."

    # ── 2. Must start with SELECT ──────────────────────────────────────────
    if not sql_upper.lstrip().startswith("SELECT"):
        return False, "Only SELECT queries are allowed. Got: " + sql_clean[:30]

    # ── 3. Forbidden write/DDL keywords ───────────────────────────────────
    # Use word-boundary regex to avoid false positives (e.g. "DELETED_AT")
    for keyword in WRITE_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, sql_upper):
            return False, f"Forbidden keyword detected: {keyword}"

    # ── 4. Forbidden tables ────────────────────────────────────────────────
    for table in FORBIDDEN_TABLES:
        if re.search(rf"\b{table}\b", sql_clean, re.IGNORECASE):
            return False, f"Access to table '{table}' is not allowed"

    # ── 5. Injection patterns ──────────────────────────────────────────────
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sql_single, re.IGNORECASE | re.DOTALL):
            return False, f"Potential SQL injection pattern detected"

    # ── 6. Must have LIMIT ─────────────────────────────────────────────────
    if "LIMIT" not in sql_upper:
        return False, "Query must include a LIMIT clause to prevent large data dumps"

    # ── 7. LIMIT value must be reasonable ─────────────────────────────────
    limit_match = re.search(r"\bLIMIT\s+(\d+)", sql_upper)
    if limit_match:
        limit_val = int(limit_match.group(1))
        if limit_val > 100:
            return False, f"LIMIT {limit_val} exceeds maximum allowed (100)"

    # ── 8. Join count ──────────────────────────────────────────────────────
    join_count = len(re.findall(r"\bJOIN\b", sql_upper))
    if join_count > MAX_JOIN_COUNT:
        return False, f"Too many JOINs ({join_count}). Max allowed: {MAX_JOIN_COUNT}"

    # ── 9. Subquery depth ──────────────────────────────────────────────────
    # Count nested SELECTs (first one is the main query)
    select_count = len(re.findall(r"\bSELECT\b", sql_upper))
    if select_count - 1 > MAX_SUBQUERIES:
        return False, f"Too many nested subqueries ({select_count - 1}). Max: {MAX_SUBQUERIES}"

    # ── 10. customer_id isolation check ───────────────────────────────────
    # If the query touches orders or customers, it MUST filter by customer_id
    touches_customer_tables = any(
        re.search(rf"\b{t}\b", sql_clean, re.IGNORECASE)
        for t in ["orders", "customers"]
    )
    if touches_customer_tables:
        if customer_id not in sql_clean:
            return False, "Queries on orders/customers must filter by customer_id"

    return True, "OK"


def sanitise_llm_output(raw: str) -> str:
    """
    Clean up the raw LLM output to extract just the SQL string.
    LLMs sometimes wrap SQL in markdown code blocks or add explanations.
    """
    if not raw:
        return ""

    text = raw.strip()

    # Remove markdown code fences  ```sql ... ``` or ``` ... ```
    text = re.sub(r"```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    # If the model added an explanation before/after, extract just the SQL
    # Look for the first SELECT keyword
    match = re.search(r"(SELECT\b.+)", text, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Remove trailing semicolons (safe to remove — we add none)
    text = text.rstrip(";").strip()

    return text