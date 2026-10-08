import os, sqlite3, tempfile, unittest
import database

class AuthDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.old = database.DB_PATH
        database.DB_PATH = self.tmp.name
        database.init_db(force=True)
        self.conn = sqlite3.connect(self.tmp.name)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close(); database.DB_PATH=self.old
        try: os.remove(self.tmp.name)
        except OSError: pass

    def test_admin_is_exact_account(self):
        rows=self.conn.execute("SELECT username, role, is_demo FROM users WHERE role='Admin'").fetchall()
        self.assertEqual([(r['username'],r['role'],r['is_demo']) for r in rows],[('admin_123','Admin',0)])
        self.assertFalse(self.conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone())

    def test_demo_accounts_are_not_login_accounts(self):
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM users WHERE is_demo=1").fetchone()[0],9)

    def test_required_tables_exist(self):
        names={r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn('referee_profiles', names)

    def test_security_files_exist(self):
        self.assertTrue((os.path.join(os.path.dirname(__file__), '..', 'auth-guard.js')))
        self.assertTrue((os.path.join(os.path.dirname(__file__), '..', 'identity-sync.js')))

if __name__ == '__main__': unittest.main()
