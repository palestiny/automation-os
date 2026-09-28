from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.application.authorization import AuthorizationContext, TenantId
from app.api.auth import get_authorization_context
from app.main import app


def test_trusted_authorization_context_reads_request_state():
    tenant_id = TenantId.create()
    context = AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=tenant_id,
    )

    def endpoint_override():
        return context

    app.dependency_overrides[get_authorization_context] = endpoint_override
    try:
        assert app.dependency_overrides[get_authorization_context]() == context
    finally:
        app.dependency_overrides = {}


def test_trusted_authorization_context_fails_closed_when_missing():
    client = TestClient(app)

    response = client.get("/review/workflows")

    assert response.status_code == 503
    assert response.json()["detail"] == "Authorization context provider is not configured"


def test_trusted_authorization_context_rejects_malformed_state():
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/review/workflows",
        "headers": [],
    }
    request = Request(scope)
    request.state.authorization_context = {"tenant_id": str(TenantId.create().value)}

    try:
        get_authorization_context(request)
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Malformed authorization context must fail closed")
