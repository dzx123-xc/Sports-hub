"""Small RFC 6238 TOTP verifier for privileged administrator sign-in.

Set ADMIN_TOTP_SECRET to a Base32 secret stored in the deployment secret manager.
The secret is never returned by an API.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time


def verify_totp(secret: str, code: str, *, now: float | None = None, window: int = 1) -> bool:
    """Verify a six-digit TOTP with a small clock-skew window."""
    normalized = "".join(str(code or "").split())
    if not secret or len(normalized) != 6 or not normalized.isdigit():
        return False
    try:
        key = base64.b32decode(secret.strip().replace(" ", "").upper() + "=" * ((8 - len(secret.strip().replace(" ", "")) % 8) % 8), casefold=True)
    except (ValueError, TypeError):
        return False
    timestamp = int((time.time() if now is None else now) // 30)
    for offset in range(-max(0, window), max(0, window) + 1):
        digest = hmac.new(key, struct.pack(">Q", timestamp + offset), hashlib.sha1).digest()
        index = digest[-1] & 0x0F
        value = (struct.unpack(">I", digest[index:index + 4])[0] & 0x7FFFFFFF) % 1_000_000
        if hmac.compare_digest(f"{value:06d}", normalized):
            return True
    return False
