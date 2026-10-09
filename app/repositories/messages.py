"""SQL-only repository for direct messages."""
from __future__ import annotations

from app.repositories.database import connection


def active_user(user_id: int) -> bool:
    with connection() as conn:
        return conn.cursor().execute("SELECT 1 FROM users WHERE id = ? AND status = 'active'", (user_id,)).fetchone() is not None


def list_conversation(user_id: int, other_id: int | None = None) -> list[dict]:
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
        return [dict(row) for row in rows]


def create_message(sender_id: int, recipient_id: int, message_text: str, message_type: str, timestamp: str) -> dict:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender_id, recipient_id, message_text, message_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            (sender_id, recipient_id, message_text, message_type, timestamp),
        )
        message_id = cursor.lastrowid
        conn.commit()
        row = cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return dict(row)
