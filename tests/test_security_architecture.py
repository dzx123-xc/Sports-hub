import unittest
from unittest.mock import patch

from app.security.totp import verify_totp
from app.storage.supabase_private import StorageNotConfigured, SupabasePrivateStorage


class TotpTests(unittest.TestCase):
    def test_rfc6238_six_digit_vector(self):
        # RFC 6238 SHA-1 test secret; at Unix time 59 the 6-digit code is 287082.
        self.assertTrue(verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "287082", now=59, window=0))

    def test_totp_rejects_wrong_code_and_malformed_secret(self):
        self.assertFalse(verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "000000", now=59, window=0))
        self.assertFalse(verify_totp("not-base32!", "287082", now=59, window=0))
        self.assertFalse(verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "12345", now=59))

    def test_private_storage_fails_closed_without_secrets(self):
        with patch.dict("os.environ", {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "", "SUPABASE_MEDIA_BUCKET": ""}):
            with self.assertRaises(StorageNotConfigured):
                SupabasePrivateStorage()


class ArchitectureContractTests(unittest.TestCase):
    def test_job_queue_schema_and_readiness_router_are_wired(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        schema = (root / "database.py").read_text(encoding="utf-8")
        main = (root / "app/main.py").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS background_jobs", schema)
        self.assertIn("app.include_router(health_router)", main)
        self.assertIn("def database_ready()", (root / "app/services/readiness.py").read_text(encoding="utf-8"))

    def test_admin_totp_can_be_enforced_by_configuration(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        server = (root / "server.py").read_text(encoding="utf-8")
        self.assertIn("ADMIN_TOTP_SECRET", server)
        self.assertIn("verify_totp(totp_secret, body.get('totp_code', ''))", server)
        self.assertIn("ADMIN_TOTP_REQUIRED", server)


if __name__ == "__main__":
    unittest.main()
