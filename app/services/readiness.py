"""Application readiness service kept separate from HTTP routing."""
from __future__ import annotations

from app.repositories.database import connection


def database_ready() -> bool:
    try:
        with connection() as conn:
            conn.cursor().execute("SELECT 1")
            return True
    except Exception:
        return False
