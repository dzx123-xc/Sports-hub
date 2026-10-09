"""Resolve legacy-compatible user/admin sessions for FastAPI request handlers."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from fastapi import Request

from app.repositories.database import connection


def principal(request: Request) -> dict | None:
    token = request.cookies.get("sc_session", "")
    admin_token = request.cookies.get("sc_admin_session", "")
    token = token or admin_token
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        row = conn.cursor().execute(
            "SELECT user_id, role, expires_at FROM sessions WHERE token_hash = ? AND expires_at > ?",
            (token_hash, now),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    if admin_token and data.get("role") == "admin":
        return {"is_admin": True, "user_id": None, "role": "Admin"}
    if token and data.get("role") == "user" and data.get("user_id") is not None:
        return {"is_admin": False, "user_id": int(data["user_id"]), "role": "User"}
    return None
