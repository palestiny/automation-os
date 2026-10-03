from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.observability import (
    RequestObservabilityMiddleware,
    _normalize_request_id,
)


def test_request_id_is_preserved_when_valid():
    assert _normalize_request_id("request-123") == "request-123"


def test_request_id_is_generated_when_missing_or_invalid():
    generated = _normalize_request_id(None)
    assert generated
    assert _normalize_request_id("") != ""
    assert _normalize_request_id("a" * 129) != "a" * 129
    assert _normalize_request_id("/unsafe") != "/unsafe"


def test_request_middleware_returns_correlation_id():
    app = FastAPI()
    app.add_middleware(RequestObservabilityMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": "test-correlation-id"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-correlation-id"
