"""Opt-in background worker for notification delivery and player scoring jobs.

Run as a separate Railway worker process only after BACKGROUND_WORKER_ENABLED=true.
Jobs are idempotent and retried up to five attempts.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from app.repositories.database import connection
from app.workers.queue import claim_one, enqueue, fail, finish
from server import calculate_player_classification

logger = logging.getLogger("sportshub.worker")


def _notify(payload: dict) -> None:
    user_id = int(payload["user_id"])
    category = str(payload.get("category") or "System")[:40]
    title = str(payload["title"]).strip()[:200]
    message = str(payload["message"]).strip()[:2000]
    link = str(payload.get("link") or "")[:500] or None
    if not title or not message:
        raise ValueError("Notification title and message are required")
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ? AND status = 'active'", (user_id,))
        if not cursor.fetchone():
            raise ValueError("Notification target is missing or inactive")
        cursor.execute(
            "INSERT INTO notifications (user_id, category, title, message, link, is_read, timestamp) VALUES (?, ?, ?, ?, ?, 0, ?)",
            (user_id, category, title, message, link, now),
        )
        conn.commit()


def _recalculate(payload: dict) -> None:
    player_id = int(payload["player_id"])
    with connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT skill_score, performance_score, progress_pct, major_matches FROM player_profiles WHERE user_id = ?",
            (player_id,),
        ).fetchone()
        if not row:
            raise ValueError("Player profile not found")
        cert_count = cursor.execute("SELECT COUNT(*) AS count FROM certificates WHERE player_id = ?", (player_id,)).fetchone()["count"]
        classification = calculate_player_classification(
            float(row["skill_score"] or 0), float(row["performance_score"] or 0),
            float(row["progress_pct"] or 0), int(row["major_matches"] or 0), int(cert_count or 0)
        )
        cursor.execute("UPDATE player_profiles SET classification = ? WHERE user_id = ?", (classification, player_id))
        conn.commit()


HANDLERS = {"notification.create": _notify, "scoring.recalculate": _recalculate}


def run_once() -> bool:
    job = claim_one()
    if not job:
        return False
    try:
        handler = HANDLERS.get(job["job_type"])
        if handler is None:
            raise ValueError(f"Unsupported job type: {job['job_type']}")
        handler(job["payload"])
        finish(int(job["id"]))
        logger.info("Completed job id=%s type=%s", job["id"], job["job_type"])
    except Exception as exc:
        logger.exception("Job failed id=%s type=%s", job.get("id"), job.get("job_type"))
        fail(int(job["id"]), str(exc))
    return True


def main() -> None:
    if os.getenv("BACKGROUND_WORKER_ENABLED", "").lower() not in ("1", "true", "yes"):
        raise SystemExit("Set BACKGROUND_WORKER_ENABLED=true before starting the worker.")
    poll_seconds = max(1, int(os.getenv("BACKGROUND_WORKER_POLL_SECONDS", "3")))
    while True:
        if not run_once():
            time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    main()
