import pytest
from starlette.requests import Request

from app.api.auth import get_authenticated_principal, get_authorization_context
from app.application.authentication import (
    AuthenticatedPrincipal,
    AuthenticationProvider,
)
from app.application.authorization import TenantId


def _request(*, headers=None, state=None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in (headers or {}).items()
        ],
        "state": state or {},
    }
    return Request(scope)


def test_authenticated_principal_requires_tenant_for_tenant_identity():
    with pytest.raises(ValueError, match="tenant"):
        AuthenticatedPrincipal(principal_id="user-1", tenant_id=None)


def test_authenticated_principal_translates_to_tenant_authorization_context():
    tenant = TenantId.create()
    principal = AuthenticatedPrincipal(
        principal_id="user-1",
        tenant_id=tenant,
    )

    context = principal.to_authorization_context()

    assert context.principal_id == "user-1"
    assert context.tenant_id == tenant
    assert context.is_system is False


def test_system_principal_translates_to_system_context():
    principal = AuthenticatedPrincipal(
        principal_id="system-service",
        tenant_id=None,
        is_system=True,
    )

    context = principal.to_authorization_context()

    assert context.is_system is True
    assert context.tenant_id is None


def test_api_reads_only_trusted_authenticated_principal_state():
    principal = AuthenticatedPrincipal(
        principal_id="user-1",
        tenant_id=TenantId.create(),
    )

    request = _request(
        headers={
            "X-User-Id": "attacker",
            "X-Tenant-Id": str(TenantId.create().value),
        },
        state={"authenticated_principal": principal},
    )

    assert get_authenticated_principal(request) is principal


def test_api_does_not_accept_client_identity_headers_as_authentication():
    request = _request(
        headers={
            "X-User-Id": "attacker",
            "X-Tenant-Id": str(TenantId.create().value),
        }
    )

    with pytest.raises(Exception) as exc:
        get_authenticated_principal(request)

    assert getattr(exc.value, "status_code", None) == 503


def test_api_does_not_accept_legacy_authorization_context_state():
    tenant = TenantId.create()
    request = _request(
        state={
            "authorization_context": AuthenticatedPrincipal(
                principal_id="user-1",
                tenant_id=tenant,
            ).to_authorization_context()
        }
    )

    with pytest.raises(Exception) as exc:
        get_authenticated_principal(request)

    assert getattr(exc.value, "status_code", None) == 503


def test_authorization_context_is_derived_from_authenticated_principal():
    tenant = TenantId.create()
    principal = AuthenticatedPrincipal(principal_id="user-1", tenant_id=tenant)

    context = get_authorization_context(principal)

    assert context.tenant_id == tenant
    assert context.principal_id == "user-1"


def test_authentication_provider_is_a_port():
    class FakeProvider:
        def authenticate(self, request: object) -> AuthenticatedPrincipal:
            return AuthenticatedPrincipal(
                principal_id="user-1",
                tenant_id=TenantId.create(),
            )

    provider: AuthenticationProvider = FakeProvider()

    assert provider.authenticate(object()).principal_id == "user-1"
