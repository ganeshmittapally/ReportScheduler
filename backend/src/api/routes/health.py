"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
import sys

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    python_version: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    status: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Liveness probe endpoint.

    Returns 200 if the application is running.
    Used by Kubernetes/Container Apps for liveness checks.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )


@router.get("/health/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe endpoint.

    Checks if the application can handle requests (database, Redis, etc. are accessible).
    Returns 200 if ready, 503 if not ready.

    TODO Phase 1: Add actual database and Redis connectivity checks.
    """
    checks = {
        "database": "not_implemented",  # TODO: Check PostgreSQL connection
        "redis": "not_implemented",  # TODO: Check Redis connection
        "service_bus": "not_implemented",  # TODO: Check Service Bus connection
    }

    # For now, always return healthy
    # In Phase 1, implement actual health checks
    return ReadinessResponse(status="ready", checks=checks)


@router.get("/", include_in_schema=False)
async def root() -> Dict[str, str]:
    """Root endpoint redirect to docs."""
    return {
        "message": "Report Scheduler API",
        "docs": "/api-docs",
        "health": "/health",
    }
