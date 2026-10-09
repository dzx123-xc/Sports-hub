"""Minimal private Supabase Storage adapter using the Storage REST API.

Configure SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and a private
SUPABASE_MEDIA_BUCKET. Never expose the service-role key to the browser.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


class StorageNotConfigured(RuntimeError):
    pass


class SupabasePrivateStorage:
    def __init__(self) -> None:
        self.base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.bucket = os.getenv("SUPABASE_MEDIA_BUCKET", "")
        if not (self.base_url.startswith("https://") and self.service_key and self.bucket):
            raise StorageNotConfigured("Private storage is not configured")

    def _request(self, method: str, path: str, body: bytes | None = None, content_type: str = "application/json") -> dict:
        url = f"{self.base_url}/storage/v1{path}"
        req = urllib.request.Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": content_type,
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = response.read()
                return json.loads(payload.decode("utf-8")) if payload else {"ok": True}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Private storage request failed ({exc.code}): {detail}") from exc

    def upload(self, object_path: str, content: bytes, content_type: str) -> dict:
        safe_path = "/".join(urllib.parse.quote(part, safe="") for part in object_path.strip("/").split("/") if part)
        if not safe_path or ".." in object_path.split("/") or not content:
            raise ValueError("A safe object path and non-empty content are required")
        return self._request("POST", f"/object/{urllib.parse.quote(self.bucket, safe='')}/{safe_path}", content, content_type)

    def create_signed_url(self, object_path: str, expires_in: int = 300) -> str:
        if not 1 <= expires_in <= 3600:
            raise ValueError("Signed URL expiry must be between 1 and 3600 seconds")
        safe_path = "/".join(urllib.parse.quote(part, safe="") for part in object_path.strip("/").split("/") if part)
        if not safe_path or ".." in object_path.split("/"):
            raise ValueError("Unsafe object path")
        result = self._request("POST", f"/object/sign/{urllib.parse.quote(self.bucket, safe='')}/{safe_path}", json.dumps({"expiresIn": expires_in}).encode(), "application/json")
        signed = result.get("signedURL") or result.get("signedUrl")
        if not signed:
            raise RuntimeError("Storage did not return a signed URL")
        return signed if signed.startswith("https://") else f"{self.base_url}/storage/v1{signed}"

    def delete(self, object_path: str) -> dict:
        safe_path = "/".join(urllib.parse.quote(part, safe="") for part in object_path.strip("/").split("/") if part)
        if not safe_path or ".." in object_path.split("/"):
            raise ValueError("Unsafe object path")
        return self._request("DELETE", f"/object/{urllib.parse.quote(self.bucket, safe='')}", json.dumps({"prefixes": [object_path.strip("/")]}).encode(), "application/json")
