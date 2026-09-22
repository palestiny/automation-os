from uuid import uuid4

import pytest

from app.application.authorization import (
    AuthorizationContext,
    AuthorizationDeniedError,
    AuthorizationPolicy,
    TenantId,
)


def test_context_requires_tenant_for_tenant_operation():
    with pytest.raises(ValueError, match="tenant"):
        AuthorizationContext(principal_id="user-1", tenant_id=None)


def test_same_tenant_is_authorized():
    tenant = TenantId.create()
    context = AuthorizationContext(principal_id="user-1", tenant_id=tenant)

    AuthorizationPolicy().require_tenant(context, tenant)


def test_cross_tenant_access_is_denied():
    context = AuthorizationContext(
        principal_id="user-1",
        tenant_id=TenantId.create(),
    )

    with pytest.raises(AuthorizationDeniedError, match="tenant"):
        AuthorizationPolicy().require_tenant(context, TenantId.create())


def test_system_operation_requires_explicit_system_context():
    tenant = TenantId.create()
    context = AuthorizationContext(principal_id="user-1", tenant_id=tenant)

    with pytest.raises(AuthorizationDeniedError, match="System"):
        AuthorizationPolicy().require_system(context)


def test_system_context_is_explicit():
    context = AuthorizationContext.system(principal_id="system-service")

    AuthorizationPolicy().require_system(context)
    assert context.is_system is True
    assert context.tenant_id is None


def test_tenant_persistence_builder_requires_durable_isolation(monkeypatch):
    from app.core import execution_dependencies

    tenant = TenantId.create()
    context = AuthorizationContext(principal_id="user-1", tenant_id=tenant)
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        execution_dependencies.build_tenant_persistence(context)


def test_tenant_persistence_builder_propagates_tenant_to_persistence(monkeypatch):
    from app.core import execution_dependencies

    tenant = TenantId.create()
    context = AuthorizationContext(principal_id="user-1", tenant_id=tenant)
    captured = {}

    monkeypatch.setenv("AUTOMATION_OS_DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(
        execution_dependencies,
        "_build_persistence",
        lambda tenant_id=None: captured.setdefault("tenant_id", tenant_id),
    )

    execution_dependencies.build_tenant_persistence(context)

    assert captured["tenant_id"] == tenant.value


def test_system_persistence_context_is_explicit(monkeypatch):
    from app.core import execution_dependencies

    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)
    context = AuthorizationContext.system(principal_id="system-service")

    repositories = execution_dependencies.build_tenant_persistence(context)

    assert repositories
