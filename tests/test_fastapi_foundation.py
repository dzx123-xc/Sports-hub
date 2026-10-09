import unittest

from fastapi.testclient import TestClient

from app.main import app


class FastAPIFoundationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_security_headers_are_set(self):
        response = self.client.get("/health")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(
            response.headers["referrer-policy"],
            "strict-origin-when-cross-origin",
        )


if __name__ == "__main__":
    unittest.main()
