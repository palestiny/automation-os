import hashlib
import json
from uuid import UUID

import pytest
from starlette.requests import Request

from app.application.authentication import AuthenticationError
from app.application.authorization import TenantId
from app.infrastructure.authentication import (
    AuthenticationProviderNotConfigured,
    EnvironmentApiKeyAuthenticationProvider,
)


def request_with_token(token: str | None) -> Request:
    headers = []
    if token is not None:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "state": {},
    })


def test_provider_authenticates_configured_digest():
    token = "example-random-test-key"
    tenant_id = UUID("00000000-0000-4000-8000-000000000001")
    configuration = json.dumps([{
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "principal_id": "test-user",
        "tenant_id": str(tenant_id),
    }])
    provider = EnvironmentApiKeyAuthenticationProvider(configuration)
    principal = provider.authenticate(request_with_token(token))
    assert principal.principal_id == "test-user"
    assert principal.tenant_id == TenantId(tenant_id)


def test_provider_rejects_missing_and_invalid_tokens():
    token = "known-test-token"
    configuration = json.dumps([{
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "principal_id": "test-user",
        "tenant_id": "00000000-0000-4000-8000-000000000001",
    }])
    provider = EnvironmentApiKeyAuthenticationProvider(configuration)
    with pytest.raises(AuthenticationError):
        provider.authenticate(request_with_token(None))
    with pytest.raises(AuthenticationError):
        provider.authenticate(request_with_token("invalid"))


def test_unconfigured_provider_fails_closed():
    provider = EnvironmentApiKeyAuthenticationProvider("")
    assert not provider.is_configured
    with pytest.raises(AuthenticationProviderNotConfigured):
        provider.authenticate(request_with_token(None))


def test_invalid_digest_configuration_is_rejected():
    with pytest.raises(ValueError, match="SHA-256"):
        EnvironmentApiKeyAuthenticationProvider(json.dumps([{
            "token_sha256": "bad",
            "principal_id": "test-user",
            "tenant_id": "00000000-0000-4000-8000-000000000001",
        }]))
