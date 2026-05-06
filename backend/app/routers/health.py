from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the current health status of the API and its downstream services.",
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.app_env,
        services={
            "ai_service": "mock" if settings.use_mock_ai else "live",
            "storage": "local",
        },
    )
