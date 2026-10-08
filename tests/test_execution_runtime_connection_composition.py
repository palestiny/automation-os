from uuid import uuid4

from app.application.authorization import AuthorizationContext, TenantId
from app.core import execution_dependencies


def test_build_execution_use_cases_injects_runtime_preparer_into_step_executor(
    monkeypatch,
):
    tenant_id = TenantId(uuid4())
    context = AuthorizationContext(
        principal_id="principal",
        tenant_id=tenant_id,
    )

    class FakePreparer:
        pass

    preparer = FakePreparer()

    monkeypatch.setattr(
        execution_dependencies,
        "build_tenant_persistence",
        lambda _context: (
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
        ),
    )
    monkeypatch.setattr(
        execution_dependencies,
        "_build_runtime_connection_preparer",
        lambda _context: preparer,
    )

    use_cases = execution_dependencies.build_execution_use_cases(context)

    assert use_cases is not None
    assert use_cases.retry_and_execute_execution._execute_workflow._step_executor._runtime_connection_preparer is preparer
