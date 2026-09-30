from uuid import uuid4

import pytest

from app.application.authorization import AuthorizationContext, TenantId
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.core import execution_dependencies


class FakeConnection:
    pass


class FakeConnectionFactory:
    def __call__(self):
        return self

    def __enter__(self):
        return FakeConnection()

    def __exit__(self, exc_type, exc, tb):
        return False


def test_tenant_runtime_connection_preparer_is_composed_inside_tenant_scope(
    monkeypatch,
):
    tenant_id = TenantId(uuid4())
    context = AuthorizationContext(
        principal_id="principal",
        tenant_id=tenant_id,
    )
    factory = FakeConnectionFactory()
    captured = {}

    class FakeConnectionRepository:
        def __init__(self, connection_factory, tenant_id=None):
            captured["factory"] = connection_factory
            captured["tenant_id"] = tenant_id

    monkeypatch.setenv("AUTOMATION_OS_DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(
        execution_dependencies,
        "postgres_connection_factory",
        lambda _: factory,
    )
    monkeypatch.setattr(
        execution_dependencies.PostgresSchema,
        "initialize",
        lambda connection: None,
    )
    monkeypatch.setattr(
        execution_dependencies,
        "PostgresConnectionRepository",
        FakeConnectionRepository,
    )

    preparer = execution_dependencies._build_runtime_connection_preparer(context)

    assert isinstance(preparer, PrepareWorkflowRuntimeConnections)
    assert captured["factory"] is factory
    assert captured["tenant_id"] == tenant_id.value


def test_system_runtime_connection_preparer_is_not_composed():
    context = AuthorizationContext.system("system")

    assert execution_dependencies._build_runtime_connection_preparer(context) is None


def test_tenant_runtime_connections_fail_closed_without_durable_persistence(
    monkeypatch,
):
    tenant_id = TenantId(uuid4())
    context = AuthorizationContext(
        principal_id="principal",
        tenant_id=tenant_id,
    )
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    with pytest.raises(
        RuntimeError,
        match="Tenant-scoped runtime connections require durable PostgreSQL configuration",
    ):
        execution_dependencies._build_runtime_connection_preparer(context)
