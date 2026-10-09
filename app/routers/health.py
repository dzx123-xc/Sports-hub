"""Health and readiness routes for the staged FastAPI application."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.readiness import database_ready

router = APIRouter(tags=["health"])


@router.get("/health/ready", include_in_schema=False)
def readiness() -> JSONResponse:
    ready = database_ready()
    return JSONResponse(
        {"status": "ready" if ready else "not_ready", "database": "ok" if ready else "unavailable"},
        status_code=200 if ready else 503,
    )
