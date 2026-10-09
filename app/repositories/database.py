"""Database access boundary for the staged FastAPI migration."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Any

from database import get_db


@contextmanager
def connection() -> Iterator[Any]:
    """Yield one configured SQLite/PostgreSQL connection and always close it."""
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()
