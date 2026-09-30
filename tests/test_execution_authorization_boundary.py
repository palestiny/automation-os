import pytest
from fastapi import APIRouter

from app.api.execution import router
from app.application.authorization import AuthorizationContext, TenantId
from app.core import execution_dependencies


def test_execution_api_requires_authorization_context_on_every_route():
    protected_routes = [
        route
        for route in router.routes
        if getattr(route, "methods", None)
    ]

    assert protected_routes
    for route in protected_routes:
        assert any(
            getattr(dependency.call, "__name__", None) == "get_authorization_context"
            for dependency in route.dependant.dependencies
        )


def test_execution_use_case_composition_accepts_explicit_system_context(monkeypatch):
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    context = AuthorizationContext.system("system-service")
    services = execution_dependencies.build_execution_use_cases(context)

    assert services.start_workflow_execution is not None
    assert services.execution_progress is not None
    assert services.discover_executions is not None
    assert services.cancel_execution is not None
    assert services.resume_execution is not None
    assert services.retry_execution is not None
    assert services.retry_and_execute_execution is not None


def test_execution_use_case_composition_rejects_unauthorized_context_type():
    with pytest.raises(TypeError, match="AuthorizationContext"):
        execution_dependencies.build_execution_use_cases(object())


def test_execution_use_case_composition_requires_durable_tenant_scope(monkeypatch):
    tenant = TenantId.create()
    context = AuthorizationContext(
        principal_id="tenant-user",
        tenant_id=tenant,
    )
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        execution_dependencies.build_execution_use_cases(context)
