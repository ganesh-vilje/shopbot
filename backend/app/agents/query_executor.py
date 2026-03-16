"""
Stage 3 — Query Executor
Runs the parameterised SQL against PostgreSQL and returns rows as dicts.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any


MAX_ROWS = 50
TIMEOUT_MS = 5000


def execute_query(db: Session, sql: str, params: dict[str, Any]) -> list[dict]:
    try:
        db.execute(text(f"SET LOCAL statement_timeout = {TIMEOUT_MS}"))
        result = db.execute(text(sql), params)
        keys = list(result.keys())
        rows = []
        for row in result.fetchmany(MAX_ROWS):
            rows.append({k: _serialise(v) for k, v in zip(keys, row)})
        return rows
    except Exception as e:
        print(f"[QueryExecutor] Error: {e}")
        return []


def _serialise(v: Any) -> Any:
    """Convert non-JSON-serialisable types."""
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "__float__"):
        return float(v)
    return v
