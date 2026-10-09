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


    def test_landing_page_never_trusts_stale_browser_identity(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('value="password123"', index)
        self.assertIn("const endpoint = isAdmin ? '/api/admin/session' : '/api/auth/me';", index)
        self.assertIn("credentials: 'same-origin'", index)
        self.assertIn("localStorage.removeItem('sporthubUser');", index)


    def test_player_discovery_filters_private_profiles(self):
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn("LEFT JOIN privacy_settings ps ON ps.user_id = u.id", server)
        self.assertIn("COALESCE(ps.profile_visibility, 'public') = 'public'", server)
        self.assertIn("c.status = 'accepted'", server)

    def test_certificate_verification_requires_admin_session(self):
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        route = server.split("elif path.startswith('/api/certificates/') and path.endswith('/verify'):", 1)[1]
        self.assertIn("if not is_admin_request(self):", route[:250])
        self.assertNotIn("body.get('admin_name'", route[:700])

    def test_registration_accepts_only_public_roles(self):
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn("if role not in ('Player', 'Coach', 'Club', 'Organizer', 'Referee'):", server)

    def test_message_and_report_inputs_are_validated(self):
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn("You cannot message your own account.", server)
        self.assertIn("Message must contain 1–5000 characters.", server)
        self.assertIn("You cannot report your own account.", server)
        self.assertIn("Report description must contain 1–5000 characters.", server)

    def test_report_submission_never_returns_fake_success_on_api_failure(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("success: false", app)
        self.assertIn("Your report was not submitted.", app)
        self.assertNotIn("return { success: true, report_id: 1024, status: 'Under Review' };", app)
        self.assertIn("Report could not be submitted. Please try again.", app)

if __name__ == "__main__":
    unittest.main()
