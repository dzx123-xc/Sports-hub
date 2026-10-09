"""Queue lease recovery regression tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from app.repositories.database import connection
from app.workers.queue import claim_one


class BackgroundQueueLeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "queue.sqlite")
        self.path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.path_patch.start()
        database.init_db(force=True)

    def tearDown(self):
        self.path_patch.stop()
        self.temp.cleanup()

    def _insert_stale_job(self, attempts):
        with connection() as conn:
            conn.cursor().execute(
                "INSERT INTO background_jobs (job_type, payload_json, status, attempts, created_at, updated_at) VALUES (?, ?, 'processing', ?, ?, ?)",
                ("notification.create", "{}", attempts, "2000-01-01T00:00:00", "2000-01-01T00:00:00"),
            )
            conn.commit()

    def test_claim_recovers_expired_processing_job(self):
        self._insert_stale_job(1)
        job = claim_one(lease_seconds=60)
        self.assertIsNotNone(job)
        self.assertEqual(job["job_type"], "notification.create")
        self.assertEqual(job["attempts"], 2)

    def test_expired_job_at_retry_limit_is_dead_lettered(self):
        self._insert_stale_job(5)
        self.assertIsNone(claim_one(lease_seconds=60))
        with connection() as conn:
            row = conn.cursor().execute("SELECT status FROM background_jobs").fetchone()
        self.assertEqual(row["status"], "failed")

    def test_lease_duration_must_be_positive(self):
        with self.assertRaises(ValueError):
            claim_one(lease_seconds=0)


if __name__ == "__main__":
    unittest.main()
