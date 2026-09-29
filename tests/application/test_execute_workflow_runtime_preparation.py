from uuid import uuid4

from app.application.execute_workflow_runtime_preparation import ExecuteWorkflowRuntimePreparation
from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PreparedRuntimeConnections


def test_runtime_preparation_application_seam_delegates():
    version = object()
    tenant_id = uuid4()
    context = ExecutionContext()
    expected = PreparedRuntimeConnections(())

    class FakePreparation:
        def __init__(self):
            self.args = None

        def prepare(self, **kwargs):
            self.args = kwargs
            return expected

    preparation = FakePreparation()
    result = ExecuteWorkflowRuntimePreparation(preparation).prepare(
        workflow_version=version, tenant_id=tenant_id, context=context
    )

    assert result is expected
    assert preparation.args == {
        "workflow_version": version,
        "tenant_id": tenant_id,
        "context": context,
    }
