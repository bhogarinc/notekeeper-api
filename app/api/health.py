"""Health check endpoints."""
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.common import HealthStatus, ReadyStatus, SuccessResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=SuccessResponse[HealthStatus],
    summary="Health check",
    description="Returns overall health status of the API.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check(db: Session = Depends(get_db)) -> SuccessResponse[HealthStatus]:
    """
    Check API health status including database connectivity.
    
    Returns:
        Health status with component checks
    """
    checks: dict[str, Any] = {}
    overall_status = "healthy"
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    health_data = HealthStatus(
        status=overall_status,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )
    
    return SuccessResponse(
        data=health_data,
        message="Health check completed"
    )


@router.get(
    "/ready",
    response_model=SuccessResponse[ReadyStatus],
    summary="Readiness check",
    description="Returns whether the service is ready to accept traffic.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"}
    }
)
async def readiness_check(db: Session = Depends(get_db)) -> SuccessResponse[ReadyStatus]:
    """
    Check if service is ready to accept traffic.
    
    Returns:
        Readiness status with dependency checks
    """
    dependencies: dict[str, bool] = {}
    is_ready = True
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        dependencies["database"] = True
    except Exception:
        dependencies["database"] = False
        is_ready = False
    
    ready_data = ReadyStatus(
        ready=is_ready,
        dependencies=dependencies
    )
    
    return SuccessResponse(
        data=ready_data,
        message="Readiness check completed"
    )


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Returns Prometheus-compatible metrics (placeholder).",
    include_in_schema=False
)
async def metrics() -> str:
    """
    Return Prometheus metrics.
    
    Returns:
        Prometheus-formatted metrics
    """
    # In production, integrate with prometheus-client
    metrics_data = f"""# HELP notekeeper_health Health status
# TYPE notekeeper_health gauge
notekeeper_health{{version="{settings.VERSION}"}} 1

# HELP notekeeper_uptime_seconds Uptime in seconds
# TYPE notekeeper_uptime_seconds counter
notekeeper_uptime_seconds {datetime.now(timezone.utc).timestamp()}
"""
    return metrics_data
