"""Small persistent job queue primitives; handlers must be idempotent.

The worker is intentionally opt-in until the queue table migration and
operational worker process are configured in each environment.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.repositories.database import connection


def enqueue(job_type: str, payload: dict[str, Any]) -> int:
    if not job_type or len(job_type) > 100:
        raise ValueError("Invalid job type")
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO background_jobs (job_type, payload_json, status, attempts, created_at, updated_at) VALUES (?, ?, 'pending', 0, ?, ?)",
            (job_type, json.dumps(payload, separators=(",", ":")), now, now),
        )
        row = cursor.execute("SELECT MAX(id) AS id FROM background_jobs").fetchone()
        conn.commit()
        return int(row["id"])


def claim_one() -> dict[str, Any] | None:
    """Claim one pending job; SQLite deployments should run a single worker."""
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM background_jobs WHERE status = 'pending' ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        job = dict(row)
        cursor.execute("UPDATE background_jobs SET status = 'processing', attempts = attempts + 1, updated_at = ? WHERE id = ? AND status = 'pending'", (now, job["id"]))
        if cursor.rowcount != 1:
            conn.rollback()
            return None
        conn.commit()
        job["payload"] = json.loads(job.pop("payload_json"))
        job["attempts"] = int(job.get("attempts") or 0) + 1
        return job


def finish(job_id: int) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        conn.cursor().execute("UPDATE background_jobs SET status = 'completed', updated_at = ?, error_text = NULL WHERE id = ?", (now, job_id))
        conn.commit()


def fail(job_id: int, error: str, max_attempts: int = 5) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with connection() as conn:
        conn.cursor().execute(
            "UPDATE background_jobs SET status = CASE WHEN attempts >= ? THEN 'failed' ELSE 'pending' END, error_text = ?, updated_at = ? WHERE id = ?",
            (max_attempts, str(error)[:1000], now, job_id),
        )
        conn.commit()
