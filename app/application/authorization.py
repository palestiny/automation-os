from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TenantId:
    value: UUID

    @classmethod
    def create(cls) -> "TenantId":
        return cls(uuid4())


@dataclass(frozen=True)
class AuthorizationContext:
    principal_id: str
    tenant_id: TenantId | None
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("Principal id cannot be empty")
        if self.is_system and self.tenant_id is not None:
            raise ValueError("System context cannot carry a tenant")
        if not self.is_system and self.tenant_id is None:
            raise ValueError("Tenant context is required for tenant operations")

    @classmethod
    def system(cls, principal_id: str) -> "AuthorizationContext":
        return cls(principal_id=principal_id, tenant_id=None, is_system=True)


class AuthorizationDeniedError(PermissionError):
    pass


class AuthorizationPolicy:
    """Explicit application-level authorization checks."""

    @staticmethod
    def require_tenant(
        context: AuthorizationContext,
        tenant_id: TenantId,
    ) -> None:
        if context.is_system:
            return
        if context.tenant_id != tenant_id:
            raise AuthorizationDeniedError(
                "Principal is not authorized for the requested tenant"
            )

    @staticmethod
    def require_system(context: AuthorizationContext) -> None:
        if not context.is_system:
            raise AuthorizationDeniedError(
                "System authorization is required for this operation"
            )
