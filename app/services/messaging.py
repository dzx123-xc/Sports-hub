"""Business rules for direct messaging."""
from __future__ import annotations

from datetime import datetime, timezone

from app.repositories import messages as message_repository


class MessagingError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def list_messages(user_id: int, other_id: int | None = None) -> list[dict]:
    if other_id is not None and other_id == user_id:
        return message_repository.list_conversation(user_id, other_id)
    return message_repository.list_conversation(user_id, other_id)


def send_message(sender_id: int, recipient_id: int, text: str, message_type: str) -> dict:
    normalized = (text or "").strip()
    if sender_id == recipient_id:
        raise MessagingError("You cannot message your own account", 400)
    if not normalized or len(normalized) > 5000:
        raise MessagingError("Message must contain 1–5000 characters", 400)
    if message_type not in {"text", "trial_invite", "tournament_invite"}:
        raise MessagingError("Invalid message type", 400)
    if not message_repository.active_user(recipient_id):
        raise MessagingError("Recipient account not found or inactive", 404)
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    return message_repository.create_message(sender_id, recipient_id, normalized, message_type, timestamp)
