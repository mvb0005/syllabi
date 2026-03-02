"""Health-check router — no authentication required."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response body for the health endpoint."""

    status: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status.

    Always returns ``{"status": "ok"}`` if the process is alive.
    """
    return HealthResponse(status="ok")
