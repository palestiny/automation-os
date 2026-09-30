from uuid import uuid4

from app.application.execution_context import ExecutionContext
from app.application.execution_runtime_preparation import PrepareExecutionRuntime
from app.application.runtime_connection_preparation import PreparedRuntimeConnections
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def test_execution_runtime_preparation_delegates_to_connection_preparation():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    version = WorkflowVersion.create_from_workflow(workflow, 1, tenant_id=tenant_id)
    context = ExecutionContext()
    calls = []

    class FakePreparation:
        def prepare(self, **kwargs):
            calls.append(kwargs)
            return PreparedRuntimeConnections(())

    PrepareExecutionRuntime(FakePreparation()).prepare(
        workflow_version=version, tenant_id=tenant_id, context=context
    )
    assert calls == [{"workflow_version": version, "tenant_id": tenant_id, "context": context}]
