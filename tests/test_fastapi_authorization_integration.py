"""Database-backed authorization integration tests for the staged FastAPI routers."""
import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import database
from app.main import app


class FastApiAuthorizationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "integration.sqlite")
        self.db_path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_path_patch.start()
        database.init_db(force=True)
        self.client = TestClient(app)
        self.tokens = {}
        self.user_ids = {}
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = (now + timedelta(hours=1)).isoformat()
        conn = database.get_db()
        try:
            cursor = conn.cursor()
            roles = ("Player", "Coach", "Club", "Organizer", "Referee")
            for i, role in enumerate(roles, start=1):
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role, full_name, status) VALUES (?, ?, ?, ?, ?, 'active')",
                    (f"user{i}", f"user{i}@example.test", "test-hash", role, f"User {i}"),
                )
                user_id = cursor.lastrowid
                self.user_ids[role] = user_id
                self.tokens[role] = f"token-{role}"
                token_hash = hashlib.sha256(self.tokens[role].encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO sessions (token_hash, user_id, role, expires_at, created_at) VALUES (?, ?, 'user', ?, ?)",
                    (token_hash, user_id, expires, now.isoformat()),
                )
                if role == "Player":
                    cursor.execute(
                        "INSERT INTO player_profiles (user_id, sport, position) VALUES (?, 'Football', 'Forward')",
                        (user_id,),
                    )
                    cursor.execute(
                        "INSERT INTO privacy_settings (user_id, profile_visibility, stats_visibility, certs_visibility) VALUES (?, 'private', 'private', 'private')",
                        (user_id,),
                    )
            # Add two unrelated messages so conversation scoping can be verified.
            cursor.execute("INSERT INTO messages (sender_id, recipient_id, message_text, timestamp) VALUES (?, ?, 'in-thread', ?)", (self.user_ids['Player'], self.user_ids['Coach'], now.isoformat()))
            cursor.execute("INSERT INTO messages (sender_id, recipient_id, message_text, timestamp) VALUES (?, ?, 'not-in-thread', ?)", (self.user_ids['Player'], self.user_ids['Club'], now.isoformat()))
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        self.client.close()
        self.db_path_patch.stop()
        self.temp.cleanup()

    def test_private_profile_is_not_visible_to_other_account_roles(self):
        for role in ("Coach", "Club", "Organizer", "Referee"):
            response = self.client.get("/api/players/" + str(self.user_ids["Player"]), cookies={"sc_session": self.tokens[role]})
            self.assertEqual(response.status_code, 404, role)

    def test_private_profile_is_visible_to_owner(self):
        response = self.client.get("/api/players/" + str(self.user_ids["Player"]), cookies={"sc_session": self.tokens["Player"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["player"]["certificates"], [])

    def test_message_history_is_scoped_to_the_requested_conversation(self):
        response = self.client.get("/api/messages?other_id=" + str(self.user_ids["Coach"]), cookies={"sc_session": self.tokens["Player"]})
        self.assertEqual(response.status_code, 200)
        messages = response.json()["messages"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["message_text"], "in-thread")

    def test_media_upload_rejects_mismatched_file_signature(self):
        response = self.client.post(
            "/api/media",
            content=b"not actually a jpeg",
            headers={"Content-Type": "image/jpeg", "X-Media-Kind": "avatar"},
            cookies={"sc_session": self.tokens["Player"]},
        )
        self.assertEqual(response.status_code, 415)

    def test_private_media_cannot_be_accessed_across_user_boundaries(self):
        response = self.client.post(
            "/api/media/signed-url",
            json={"object_path": "user-2/avatar/private.webp"},
            cookies={"sc_session": self.tokens["Player"]},
        )
        self.assertEqual(response.status_code, 403)

    def test_certificate_visibility_is_enforced_for_other_roles(self):
        conn = database.get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO certificates (player_id, title, issuing_org, year, achievement_text) VALUES (?, 'Private award', 'Test Org', 2026, 'Private')",
                (self.user_ids["Player"],),
            )
            conn.commit()
        finally:
            conn.close()
        response = self.client.get(
            "/api/certificates?player_id=" + str(self.user_ids["Player"]),
            cookies={"sc_session": self.tokens["Coach"]},
        )
        self.assertEqual(response.status_code, 404)

    def test_certificate_owner_can_view_own_private_certificate(self):
        conn = database.get_db()
        try:
            conn.cursor().execute(
                "INSERT INTO certificates (player_id, title, issuing_org, year, achievement_text) VALUES (?, 'Private award', 'Test Org', 2026, 'Private')",
                (self.user_ids["Player"],),
            )
            conn.commit()
        finally:
            conn.close()
        response = self.client.get(
            "/api/certificates?player_id=" + str(self.user_ids["Player"]),
            cookies={"sc_session": self.tokens["Player"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["certificates"]), 1)

    def test_message_post_rejects_self_message(self):
        response = self.client.post(
            "/api/messages",
            json={"recipient_id": self.user_ids["Player"], "message_text": "self", "message_type": "text"},
            cookies={"sc_session": self.tokens["Player"]},
        )
        self.assertEqual(response.status_code, 400)

    def test_message_post_rejects_inactive_recipient(self):
        conn = database.get_db()
        try:
            conn.cursor().execute("UPDATE users SET status = 'inactive' WHERE id = ?", (self.user_ids["Coach"],))
            conn.commit()
        finally:
            conn.close()
        response = self.client.post(
            "/api/messages",
            json={"recipient_id": self.user_ids["Coach"], "message_text": "hello", "message_type": "text"},
            cookies={"sc_session": self.tokens["Player"]},
        )
        self.assertEqual(response.status_code, 404)

    def test_message_history_requires_a_session(self):
        response = self.client.get("/api/messages")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
