from fastapi import APIRouter, Response, status

from app.application.health import liveness, readiness

router = APIRouter(tags=["health"])


@router.get("/health/live")
def health_live() -> dict[str, object]:
    result = liveness()
    return {"status": result.status, "checks": result.checks}


@router.get("/health/ready")
def health_ready(response: Response) -> dict[str, object]:
    result = readiness()
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": result.status, "checks": result.checks}
