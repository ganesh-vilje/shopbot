"""
Query Executor  (Stage 3)
Runs the validated SQL string against PostgreSQL via SQLAlchemy.
No params dict needed — SQL is fully constructed by the generator.
Includes timeouts, row caps, and full error handling.
"""
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

MAX_ROWS    = 50      # hard cap on rows returned to prevent data dumps
TIMEOUT_MS  = 5000    # 5 seconds — kill slow queries


def execute_query(db: Session, sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """
    Execute a validated SQL string and return rows as a list of dicts.
    Enforces a statement timeout and row cap.
    Always safe to call — catches all exceptions and returns [] on failure.
    """
    if not sql or not sql.strip():
        return []

    try:
        # Set per-transaction timeout — prevents long-running queries
        # from holding DB connections
        db.execute(text(f"SET LOCAL statement_timeout = {TIMEOUT_MS}"))

        result = db.execute(text(sql), params or {})
        keys   = list(result.keys())
        rows   = []

        for row in result.fetchmany(MAX_ROWS):
            rows.append({
                k: _serialise(v)
                for k, v in zip(keys, row)
            })

        return rows

    except Exception as e:
        error_msg = str(e)

        # Log the error but never expose raw DB errors to the user
        if "statement_timeout" in error_msg:
            print(f"[QueryExecutor] Query timed out after {TIMEOUT_MS}ms")
        elif "syntax error" in error_msg.lower():
            print(f"[QueryExecutor] SQL syntax error: {error_msg[:200]}")
        else:
            print(f"[QueryExecutor] Execution error: {error_msg[:200]}")

        return []


def _serialise(v: Any) -> Any:
    """
    Convert DB types to JSON-safe Python types.
    Handles: datetime, Decimal, UUID, enum, bytes.
    """
    if v is None:
        return None
    if hasattr(v, "isoformat"):          # datetime, date, time
        return v.isoformat()
    if hasattr(v, "__float__"):          # Decimal
        return float(v)
    if hasattr(v, "value"):              # Python enum
        return v.value
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return v


def execute_with_fallback(
    db: Session,
    sql: str,
    search_term: str | None = None,
    params: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Execute SQL and if no results found, retry with individual words from the search term.
    
    Example:
        Search "Patagonia jacket" → 0 results
        Retry "Patagonia" → 3 results ✅
        
    This handles cases where the full phrase doesn't match but a keyword does.
    """
    # Run original query first
    rows = execute_query(db, sql, params=params)

    # If results found — return immediately, no fallback needed
    if rows:
        return rows

    # If no search term or single word — no fallback possible
    if not search_term or len(search_term.strip().split()) <= 1:
        return rows

    # Split search term into individual words and retry each one
    words = search_term.strip().split()
    
    # Filter out short/common words that would match too broadly
    meaningful_words = [w for w in words if len(w) > 3]

    for word in meaningful_words:
        print(f"[QueryExecutor] No results for '{search_term}' — retrying with '{word}'")
        
        fallback_params = dict(params or {})
        for key, value in list(fallback_params.items()):
            if value == search_term:
                fallback_params[key] = word

        fallback_rows = execute_query(db, sql, params=fallback_params)
        
        if fallback_rows:
            print(f"[QueryExecutor] ✓ Found {len(fallback_rows)} results with fallback word '{word}'")
            return fallback_rows

    print(f"[QueryExecutor] No results found even with word-by-word fallback")
    return []
