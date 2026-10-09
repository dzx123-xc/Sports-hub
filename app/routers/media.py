"""Authenticated upload and short-lived access for private avatar/video objects.

Client sends the raw file body with Content-Type and X-Media-Kind headers.
"""
from __future__ import annotations

import secrets
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.security.request_auth import principal
from app.storage.supabase_private import StorageNotConfigured, SupabasePrivateStorage

router = APIRouter(prefix="/api/media", tags=["media"])

_ALLOWED = {
    "avatar": {"image/jpeg": ("jpg", 5 * 1024 * 1024), "image/png": ("png", 5 * 1024 * 1024), "image/webp": ("webp", 5 * 1024 * 1024)},
    "video": {"video/mp4": ("mp4", 50 * 1024 * 1024), "video/webm": ("webm", 50 * 1024 * 1024)},
}


class MediaAccessRequest(BaseModel):
    object_path: str = Field(min_length=1, max_length=300)


@router.post("")
async def upload_private_media(request: Request) -> dict:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    kind = request.headers.get("X-Media-Kind", "").strip().lower()
    content_type = request.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if kind not in _ALLOWED or content_type not in _ALLOWED[kind]:
        raise HTTPException(status_code=415, detail="Unsupported media kind or content type")
    extension, max_bytes = _ALLOWED[kind][content_type]
    try:
        declared_size = int(request.headers.get("Content-Length", "0"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Content-Length")
    if declared_size <= 0 or declared_size > max_bytes:
        raise HTTPException(status_code=413, detail=f"File size must be between 1 and {max_bytes} bytes")
    body = await request.body()
    if len(body) != declared_size or len(body) > max_bytes:
        raise HTTPException(status_code=400, detail="Upload size did not match Content-Length")
    object_path = f"user-{int(actor['user_id'])}/{kind}/{secrets.token_urlsafe(18)}.{extension}"
    try:
        storage = SupabasePrivateStorage()
        storage.upload(object_path, body, content_type)
        signed_url = storage.create_signed_url(object_path, expires_in=300)
    except StorageNotConfigured:
        raise HTTPException(status_code=503, detail="Private media storage is not configured")
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Private media storage request failed")
    return {"object_path": object_path, "signed_url": signed_url, "expires_in": 300}


@router.post("/signed-url")
def private_media_signed_url(payload: MediaAccessRequest, request: Request) -> dict:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    expected_prefix = f"user-{int(actor['user_id'])}/"
    if not payload.object_path.startswith(expected_prefix) or ".." in payload.object_path.split("/"):
        raise HTTPException(status_code=403, detail="You may only access your own media")
    try:
        signed_url = SupabasePrivateStorage().create_signed_url(payload.object_path, expires_in=300)
    except StorageNotConfigured:
        raise HTTPException(status_code=503, detail="Private media storage is not configured")
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Private media storage request failed")
    return {"signed_url": signed_url, "expires_in": 300}


@router.delete("")
def delete_private_media(payload: MediaAccessRequest, request: Request) -> dict:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    expected_prefix = f"user-{int(actor['user_id'])}/"
    if not payload.object_path.startswith(expected_prefix) or ".." in payload.object_path.split("/"):
        raise HTTPException(status_code=403, detail="You may only delete your own media")
    try:
        SupabasePrivateStorage().delete(payload.object_path)
    except StorageNotConfigured:
        raise HTTPException(status_code=503, detail="Private media storage is not configured")
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Private media storage request failed")
    return {"deleted": True}
