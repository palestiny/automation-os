from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from app.application.tenant_context import Principal, Role, TenantContext, TenantId


class Permission(Enum):
    WORKFLOW_READ = "workflow.read"
    WORKFLOW_UPDATE = "workflow.update"
    WORKFLOW_DELETE = "workflow.delete"
    EXECUTION_READ = "execution.read"
    EXECUTION_CONTROL = "execution.control"
    MARKETPLACE_PRIVATE_READ = "marketplace.private.read"


class AuthorizationDenied(PermissionError):
    pass


@runtime_checkable
class AuthorizationPort(Protocol):
    def require(
        self,
        context: TenantContext | None,
        permission: Permission,
    ) -> None:
        ...

    def require_resource(
        self,
        context: TenantContext | None,
        resource_tenant: TenantId,
        permission: Permission,
    ) -> None:
        ...


class InMemoryAuthorizationPolicy(AuthorizationPort):
    """Deterministic application-level authorization policy."""

    _permissions: dict[Role, frozenset[Permission]] = {
        Role.OWNER: frozenset(Permission),
        Role.MEMBER: frozenset({
            Permission.WORKFLOW_READ,
            Permission.EXECUTION_READ,
        }),
    }

    def require(
        self,
        context: TenantContext | None,
        permission: Permission,
    ) -> None:
        if context is None:
            raise AuthorizationDenied(
                "Tenant context is required for authorized operations"
            )

        if not isinstance(permission, Permission):
            raise TypeError("permission must be a Permission")

        if not any(
            permission in self._permissions[role]
            for role in context.principal.roles
        ):
            raise AuthorizationDenied(
                f"Permission denied: {permission.value}"
            )

    def require_resource(
        self,
        context: TenantContext | None,
        resource_tenant: TenantId,
        permission: Permission,
    ) -> None:
        if context is None:
            raise AuthorizationDenied(
                "Tenant context is required for tenant-scoped resources"
            )

        if context.tenant_id != resource_tenant and not context.is_system:
            raise AuthorizationDenied("Tenant scope does not match resource tenant")

        self.require(context, permission)


def principal(subject: str, *roles: Role) -> Principal:
    return Principal.create(subject, set(roles))
