"""Message feature router; every conversation query is participant-scoped."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.security.request_auth import principal
from app.services.messaging import MessagingError, list_messages as service_list_messages, send_message as service_send_message

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessageCreate(BaseModel):
    recipient_id: int
    message_text: str = Field(min_length=1, max_length=5000)
    message_type: str = Field(default="text", pattern="^(text|trial_invite|tournament_invite)$")


def _actor(request: Request) -> int:
    actor = principal(request)
    if not actor or actor.get("is_admin") or not actor.get("user_id"):
        raise HTTPException(status_code=401, detail="User authentication required")
    return int(actor["user_id"])


@router.get("")
def list_messages(request: Request, other_id: int | None = None) -> dict:
    user_id = _actor(request)
    return {"messages": service_list_messages(user_id, other_id)}


@router.post("")
def send_message(payload: MessageCreate, request: Request) -> dict:
    sender_id = _actor(request)
    try:
        message = service_send_message(sender_id, payload.recipient_id, payload.message_text, payload.message_type)
    except MessagingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    return {"message": message}
