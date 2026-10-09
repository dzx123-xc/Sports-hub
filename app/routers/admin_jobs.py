"""Privileged endpoints to enqueue expensive maintenance jobs."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.security.request_auth import principal
from app.workers.queue import enqueue

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])


class RecalculateRequest(BaseModel):
    player_id: int = Field(gt=0)


@router.post("/recalculate-player")
def recalculate_player(payload: RecalculateRequest, request: Request) -> dict:
    actor = principal(request)
    if not actor or not actor.get("is_admin"):
        raise HTTPException(status_code=403, detail="Administrator authorization required")
    try:
        job_id = enqueue("scoring.recalculate", {"player_id": payload.player_id})
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not enqueue scoring job") from exc
    return {"queued": True, "job_id": job_id, "job_type": "scoring.recalculate"}
