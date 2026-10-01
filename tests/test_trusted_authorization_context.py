from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.application.authentication import AuthenticatedPrincipal
from app.application.authorization import TenantId
from app.api.auth import get_authenticated_principal, get_authorization_context
from app.main import app


def test_trusted_authenticated_principal_reads_request_state():
    principal = AuthenticatedPrincipal(
        principal_id="reviewer-1",
        tenant_id=TenantId.create(),
    )

    scope = {"type": "http", "method": "GET", "path": "/review/workflows", "headers": []}
    request = Request(scope)
    request.state.authenticated_principal = principal

    assert get_authenticated_principal(request) == principal


def test_trusted_authentication_fails_closed_when_missing():
    client = TestClient(app)

    response = client.get("/review/workflows")

    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication provider is not configured"


def test_trusted_authentication_rejects_malformed_state():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/review/workflows",
        "headers": [],
    }
    request = Request(scope)
    request.state.authenticated_principal = {"tenant_id": str(TenantId.create().value)}

    try:
        get_authenticated_principal(request)
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Malformed authenticated principal must fail closed")


def test_authorization_context_is_derived_from_trusted_principal():
    principal = AuthenticatedPrincipal(
        principal_id="reviewer-1",
        tenant_id=TenantId.create(),
    )
    request = Request(
        {"type": "http", "method": "GET", "path": "/", "headers": []}
    )
    request.state.authenticated_principal = principal

    assert get_authorization_context(principal).principal_id == "reviewer-1"
