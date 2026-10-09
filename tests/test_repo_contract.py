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

    def test_server_has_single_authoritative_admin_guard(self):
        text = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertEqual(text.count("def is_admin_request"), 1)
        self.assertNotIn("ADMIN_SESSIONS", text)

    def test_postgres_demo_seed_is_opt_in(self):
        text = (ROOT / "database.py").read_text(encoding="utf-8")
        self.assertIn('SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false")', text)
        self.assertIn("if not USING_POSTGRES or SEED_DEMO_DATA:", text)

    def test_protected_dashboards_load_security_scripts(self):
        for page in [
            "player-dashboard.html", "coach-dashboard.html", "club-dashboard.html",
            "organizer-dashboard.html", "referee-dashboard.html"
        ]:
            text = (ROOT / page).read_text(encoding="utf-8")
            self.assertIn('src="auth-guard.js"', text)
            self.assertIn('src="identity-sync.js"', text)


    def test_login_preserves_password_whitespace_and_logout_clears_legacy_cache(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn("password = String(password || '');", app)
        self.assertIn("pass=document.getElementById('loginPass').value;", index)
        self.assertIn("password = str(body.get('password', ''))", server)
        self.assertIn("localStorage.removeItem('sporthubUser');", app)
        self.assertIn("credentials: 'same-origin'", app)
        self.assertIn("window.location.replace('index.html?logged_out=1');", app)


    def test_admin_users_and_overview_are_loaded_from_authenticated_apis(self):
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        admin = (ROOT / "admin-portal.html").read_text(encoding="utf-8")
        self.assertIn("AS sport_or_org", server)
        self.assertIn("path == '/api/admin/users'", server)
        self.assertIn("fetch('/api/admin/users'", admin)
        self.assertIn("fetch('/api/admin/stats'", admin)
        self.assertIn('id="platformUsersBody"', admin)
        self.assertNotIn("SessionManager.switchDemoUser('player1')", admin)

if __name__ == "__main__":
    unittest.main()
