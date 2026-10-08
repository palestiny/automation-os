from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.application.authentication import (
    AuthenticatedPrincipal,
    AuthenticationError,
)
from app.application.authorization import TenantId

_SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


class AuthenticationProviderNotConfigured(RuntimeError):
    """Raised when no API key credentials have been configured."""


class EnvironmentApiKeyAuthenticationProvider:
    """Bearer API-key adapter backed by SHA-256 token digests in environment JSON.

    Configure AUTOMATION_OS_API_KEYS_JSON as a JSON array of objects with
    token_sha256, principal_id, and tenant_id; is_system=true may be used only
    for explicitly authorized system identities. Store only token digests here.
    """

    def __init__(self, configuration: str | None = None) -> None:
        raw = (
            os.environ.get("AUTOMATION_OS_API_KEYS_JSON", "")
            if configuration is None
            else configuration
        )
        self._credentials: list[tuple[str, AuthenticatedPrincipal]] = []
        if not raw.strip():
            return

        try:
            entries = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("AUTOMATION_OS_API_KEYS_JSON must be valid JSON") from exc
        if not isinstance(entries, list) or not entries:
            raise ValueError("API key configuration must be a non-empty JSON array")

        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Each API key configuration must be an object")
            digest = str(entry.get("token_sha256", "")).lower()
            if not _SHA256_PATTERN.fullmatch(digest):
                raise ValueError("Each token_sha256 must be a 64-character SHA-256 hex digest")
            if digest in seen:
                raise ValueError("Duplicate API key digest configured")
            seen.add(digest)

            is_system = entry.get("is_system", False) is True
            principal_id = str(entry.get("principal_id", "")).strip()
            tenant_raw = entry.get("tenant_id")
            if is_system:
                tenant_id = None
            else:
                try:
                    tenant_id = TenantId(UUID(str(tenant_raw)))
                except (ValueError, TypeError, AttributeError) as exc:
                    raise ValueError("Tenant API keys require a valid tenant_id UUID") from exc
            principal = AuthenticatedPrincipal(
                principal_id=principal_id,
                tenant_id=tenant_id,
                is_system=is_system,
            )
            self._credentials.append((digest, principal))

    @property
    def is_configured(self) -> bool:
        return bool(self._credentials)

    def authenticate(self, request: object) -> AuthenticatedPrincipal:
        if not self._credentials:
            raise AuthenticationProviderNotConfigured(
                "Authentication provider is not configured"
            )
        if not isinstance(request, Request):
            raise TypeError("Authentication expects a Starlette Request")
        authorization = request.headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip():
            raise AuthenticationError("A bearer token is required")

        digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
        matched: AuthenticatedPrincipal | None = None
        for expected_digest, principal in self._credentials:
            if hmac.compare_digest(digest, expected_digest):
                matched = principal
        if matched is None:
            raise AuthenticationError("Invalid bearer token")
        return matched


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Attach only identities verified by the configured authentication adapter."""

    async def dispatch(self, request: Request, call_next) -> Response:
        provider = getattr(request.app.state, "authentication_provider", None)
        try:
            if provider is None:
                raise AuthenticationProviderNotConfigured(
                    "Authentication provider is not configured"
                )
            request.state.authenticated_principal = provider.authenticate(request)
            request.state.authentication_error = None
        except AuthenticationProviderNotConfigured:
            request.state.authenticated_principal = None
            request.state.authentication_error = "unconfigured"
        except AuthenticationError:
            request.state.authenticated_principal = None
            request.state.authentication_error = "invalid"
        response = await call_next(request)
        return response
