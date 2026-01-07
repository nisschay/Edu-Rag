"""
Health check endpoints.

Provides endpoints for:
- Application health status
- Environment information
- Future: Database connectivity checks
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Health Check",
    description="Returns the current health status and environment of the application.",
    response_description="Health status object",
)
def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """
    Check application health status.
    
    Returns:
        dict: Health status with environment information.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Checks if the application is ready to serve requests.",
    response_description="Readiness status",
)
def readiness_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | bool]:
    """
    Check if application is ready to handle requests.
    
    Future: Will include database connectivity check.
    
    Returns:
        dict: Readiness status with component health.
    """
    return {
        "status": "ready",
        "environment": settings.ENVIRONMENT,
        "database": True,  # Future: actual DB ping
    }
