"""Shared privacy authorization policy for profile, stats and certificate data."""
from __future__ import annotations


_ALLOWED_VISIBILITY = {"public", "connections_only", "private"}


def can_view_visibility(visibility: str | None, *, is_admin: bool, is_owner: bool, is_connected: bool) -> bool:
    """Fail closed for unknown visibility values; owners/admins retain access."""
    if is_admin or is_owner:
        return True
    normalized = str(visibility or "public").strip().lower()
    if normalized not in _ALLOWED_VISIBILITY:
        return False
    if normalized == "public":
        return True
    if normalized == "connections_only":
        return is_connected
    return False
