from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.authorization import AuthorizationContext, TenantId


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Trusted identity produced by an authentication adapter."""

    principal_id: str
    tenant_id: TenantId | None
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("Principal id cannot be empty")
        if self.is_system and self.tenant_id is not None:
            raise ValueError("System principal cannot carry a tenant")
        if not self.is_system and self.tenant_id is None:
            raise ValueError("Tenant principal requires a tenant")

    def to_authorization_context(self) -> AuthorizationContext:
        if self.is_system:
            return AuthorizationContext.system(self.principal_id)
        return AuthorizationContext(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
        )


class AuthenticationError(Exception):
    """Base error for authentication failures."""


class AuthenticationProvider(Protocol):
    """Infrastructure port for authenticating a request.

    Implementations may use OIDC/JWT, a platform identity service, or another
    trusted mechanism. The application layer consumes only the normalized
    principal and never parses provider-specific credentials.
    """

    def authenticate(self, request: object) -> AuthenticatedPrincipal:
        ...
