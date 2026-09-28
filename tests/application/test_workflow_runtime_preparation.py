from uuid import uuid4

from app.application.execution_context import ExecutionContext
from app.application.workflow_runtime_preparation import WorkflowRuntimePreparation


def test_workflow_runtime_preparation_delegates_to_connection_preparer():
    calls = []

    class FakePreparer:
        def prepare(self, **kwargs):
            calls.append(kwargs)

    version = object()
    tenant_id = uuid4()
    context = ExecutionContext()

    WorkflowRuntimePreparation(FakePreparer()).prepare(
        workflow_version=version, tenant_id=tenant_id, context=context
    )

    assert calls == [{"workflow_version": version, "tenant_id": tenant_id, "context": context}]
