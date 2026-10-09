"""Message feature router; every conversation query is participant-scoped."""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.repositories.database import connection
from app.security.request_auth import principal

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessageCreate(BaseModel):
    recipient_id: int
    message_text: str = Field(min_length=1, max_length=5000)
    message_type: str = Field(default="text", pattern="^(text|trial_invite|tournament_invite)$")


@router.get("")
def list_messages(request: Request, other_id: int | None = None) -> dict:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    user_id = int(actor["user_id"])
    with connection() as conn:
        cursor = conn.cursor()
        if other_id is not None:
            rows = cursor.execute("""
                SELECT m.*, u.full_name AS sender_name, u.avatar AS sender_avatar
                FROM messages m JOIN users u ON u.id = m.sender_id
                WHERE (m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?)
                ORDER BY m.timestamp ASC
            """, (user_id, other_id, other_id, user_id)).fetchall()
        else:
            rows = cursor.execute("""
                SELECT m.*, u.full_name AS sender_name, u.avatar AS sender_avatar
                FROM messages m JOIN users u ON u.id = m.sender_id
                WHERE m.sender_id = ? OR m.recipient_id = ? ORDER BY m.timestamp DESC
            """, (user_id, user_id)).fetchall()
        return {"messages": [dict(row) for row in rows]}


@router.post("")
def send_message(payload: MessageCreate, request: Request) -> dict:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    sender_id = int(actor["user_id"])
    if sender_id == payload.recipient_id:
        raise HTTPException(status_code=400, detail="You cannot message your own account")
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        cursor = conn.cursor()
        recipient = cursor.execute("SELECT id FROM users WHERE id = ? AND status = 'active'", (payload.recipient_id,)).fetchone()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient account not found or inactive")
        cursor.execute(
            "INSERT INTO messages (sender_id, recipient_id, message_text, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            (sender_id, payload.recipient_id, payload.message_text.strip(), payload.message_type, now),
        )
        conn.commit()
        row = cursor.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return {"message": dict(row)}
