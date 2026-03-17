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


def execute_query(db: Session, sql: str) -> list[dict]:
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

        result = db.execute(text(sql))
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