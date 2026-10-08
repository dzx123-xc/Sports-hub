import os, sqlite3, tempfile, unittest
import database

class AuthDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.old_path = database.DB_PATH
        self.old_backend = database.DATABASE_URL
        database.DATABASE_URL = ""
        database.USING_POSTGRES = False
        database.DB_PATH = self.tmp.name
        database.init_db(force=True)
        self.conn = sqlite3.connect(self.tmp.name)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()
        database.DB_PATH = self.old_path
        database.DATABASE_URL = self.old_backend
        database.USING_POSTGRES = bool(database.DATABASE_URL)
        try:
            os.remove(self.tmp.name)
        except OSError:
            pass

    def test_password_hashing_is_salted_and_verifiable(self):
        first = database.hash_pw("StrongPass1!")
        second = database.hash_pw("StrongPass1!")
        self.assertNotEqual(first, second)
        self.assertTrue(database.verify_pw("StrongPass1!", first))
        self.assertFalse(database.verify_pw("WrongPass1!", first))
        self.assertTrue(first.startswith("pbkdf2_sha256$"))

    def test_legacy_sha256_is_still_verifiable_for_migration(self):
        legacy = database.hashlib.sha256("password123".encode()).hexdigest()
        self.assertTrue(database.verify_pw("password123", legacy))
        self.assertFalse(database.verify_pw("wrong", legacy))

    def test_admin_is_not_stored_in_database(self):
        rows = self.conn.execute("SELECT username, role FROM users WHERE role='Admin'").fetchall()
        self.assertEqual(rows, [])

    def test_seeded_accounts_are_real_demo_records(self):
        count = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertEqual(count, 9)

    def test_required_tables_exist(self):
        names = {r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ["referee_profiles", "privacy_settings", "sessions"]:
            self.assertIn(table, names)

    def test_security_files_exist(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        self.assertTrue(os.path.isfile(os.path.join(root, "auth-guard.js")))
        self.assertTrue(os.path.isfile(os.path.join(root, "identity-sync.js")))

if __name__ == "__main__":
    unittest.main()
