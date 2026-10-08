import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class RepositoryContractTests(unittest.TestCase):
    def test_auth_guard_defines_all_protected_roles(self):
        text = (ROOT / "auth-guard.js").read_text(encoding="utf-8")
        for page, role in {
            "player-dashboard.html": "Player",
            "coach-dashboard.html": "Coach",
            "club-dashboard.html": "Club",
            "organizer-dashboard.html": "Organizer",
            "referee-dashboard.html": "Referee",
            "admin-portal.html": "Admin",
        }.items():
            self.assertIn(page, text)
            self.assertIn(role, text)

    def test_identity_sync_uses_server_session(self):
        text = (ROOT / "identity-sync.js").read_text(encoding="utf-8")
        self.assertIn("/api/auth/me", text)
        self.assertIn("credentials:'same-origin'", text)
        self.assertNotIn("Rahul Kumar", text)
        self.assertNotIn("Vikram Rathore", text)

    def test_profile_editor_uses_authenticated_profile_endpoint(self):
        text = (ROOT / "profile-editor.js").read_text(encoding="utf-8")
        self.assertIn("/api/auth/me", text)
        self.assertIn("/api/profile", text)

if __name__ == "__main__":
    unittest.main()
