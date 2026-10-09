"""FastAPI entry point for the staged SportsHub backend migration.

The deployed application still starts through server.py. Do not switch the
production start command until API compatibility and security phases are done.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from app.routers.health import router as health_router
from app.routers.players import router as players_router
from app.routers.certificates import router as certificates_router
from app.routers.messages import router as messages_router
from app.routers.media import router as media_router
from app.routers.admin_jobs import router as admin_jobs_router

app = FastAPI(
    title="SportsHub API",
    version="1.0.0",
    docs_url=None if os.getenv("RAILWAY_ENVIRONMENT_NAME") == "production" else "/docs",
    redoc_url=None,
    openapi_url=None if os.getenv("RAILWAY_ENVIRONMENT_NAME") == "production" else "/openapi.json",
)

app.include_router(health_router)
app.include_router(players_router)
app.include_router(certificates_router)
app.include_router(messages_router)
app.include_router(media_router)
app.include_router(admin_jobs_router)



@app.middleware("http")
async def baseline_security_headers(request: Any, call_next: Any) -> Response:
    """Set baseline browser security headers on every FastAPI response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    """Liveness endpoint for the isolated FastAPI foundation.

    Database readiness is intentionally not reported as healthy here yet:
    the database adapter and connection lifecycle will be wired in the
    repository migration phase. The existing production /health endpoint is
    still provided by server.py and checks the configured database.
    """
    return JSONResponse({"status": "ok", "service": "sportshub-fastapi-foundation"})
