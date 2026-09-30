from uuid import uuid4

import pytest

from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.domain.connection import ConnectionRequirement
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def test_runtime_preparation_uses_trusted_context_writer():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "youtube.primary")
        ],
    )

    class FakeResolver:
        def resolve(self, **kwargs):
            return object()

    context = ExecutionContext()
    prepared = PrepareWorkflowRuntimeConnections(FakeResolver()).prepare(
        workflow_version=version,
        tenant_id=tenant_id,
        context=context,
    )

    assert context.get_runtime_connections() is prepared


def test_runtime_connection_key_cannot_be_injected_by_caller():
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.set("runtime.connections", object())
