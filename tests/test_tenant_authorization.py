from uuid import uuid4

import pytest

from app.application.authorization import (
    AuthorizationDenied,
    AuthorizationPort,
    InMemoryAuthorizationPolicy,
    Permission,
    Principal,
    Role,
)
from app.application.tenant_context import TenantContext, TenantId


def test_tenant_context_requires_explicit_tenant():
    tenant = TenantId.create("tenant-a")
    principal = Principal.create("user-1", roles={Role.OWNER})

    context = TenantContext(tenant_id=tenant, principal=principal)

    assert context.tenant_id.value == "tenant-a"
    assert context.principal.subject == "user-1"


def test_system_scope_is_explicit():
    context = TenantContext.system()

    assert context.tenant_id == TenantId.system()
    assert context.is_system is True


def test_missing_tenant_context_is_rejected_for_tenant_operation():
    policy = InMemoryAuthorizationPolicy()

    with pytest.raises(AuthorizationDenied, match="tenant context"):
        policy.require(None, Permission.WORKFLOW_READ)


def test_owner_can_read_and_update_workflows():
    tenant = TenantId.create("tenant-a")
    principal = Principal.create("owner-1", roles={Role.OWNER})
    context = TenantContext(tenant, principal)
    policy = InMemoryAuthorizationPolicy()

    policy.require(context, Permission.WORKFLOW_READ)
    policy.require(context, Permission.WORKFLOW_UPDATE)


def test_member_can_read_but_cannot_update_workflows():
    tenant = TenantId.create("tenant-a")
    principal = Principal.create("member-1", roles={Role.MEMBER})
    context = TenantContext(tenant, principal)
    policy = InMemoryAuthorizationPolicy()

    policy.require(context, Permission.WORKFLOW_READ)

    with pytest.raises(AuthorizationDenied):
        policy.require(context, Permission.WORKFLOW_UPDATE)


def test_policy_is_tenant_scoped():
    tenant_a = TenantId.create("tenant-a")
    tenant_b = TenantId.create("tenant-b")
    principal = Principal.create("owner-1", roles={Role.OWNER})
    context_a = TenantContext(tenant_a, principal)
    policy = InMemoryAuthorizationPolicy()
    resource_tenant = tenant_b

    with pytest.raises(AuthorizationDenied, match="tenant"):
        policy.require_resource(context_a, resource_tenant, Permission.WORKFLOW_READ)


def test_principal_roles_are_deterministic_and_unique():
    principal = Principal.create(
        str(uuid4()),
        roles={Role.MEMBER, Role.MEMBER},
    )

    assert principal.roles == frozenset({Role.MEMBER})
    assert isinstance(policy_port := InMemoryAuthorizationPolicy(), AuthorizationPort)
