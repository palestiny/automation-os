from uuid import uuid4

import pytest

from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_context import ExecutionContext
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


class RecordingDispatcher:
    def __init__(self):
        self.calls = 0

    def dispatch(self, capability_id, context):
        self.calls += 1
        raise AssertionError("capability must not be invoked")


class FailingPreparer:
    def prepare(self, **kwargs):
        raise RuntimeError("connection unavailable")


def test_connection_preparation_failure_prevents_capability_invocation():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "youtube.primary")
        ],
    )
    version.publish()

    workflows = InMemoryWorkflowRepository(tenant_id=tenant_id)
    versions = InMemoryWorkflowVersionRepository(tenant_id=tenant_id)
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    versions.save(version)

    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
    )
    execution.start()
    executions.save(execution)

    dispatcher = RecordingDispatcher()
    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        dispatcher,
        type("Conditions", (), {"evaluate": lambda *args: True})(),
        versions,
        runtime_connection_preparer=FailingPreparer(),
        tenant_id=tenant_id,
    )

    with pytest.raises(RuntimeError, match="connection unavailable"):
        step_executor.execute(execution.id, ExecutionContext())

    assert dispatcher.calls == 0
    assert executions.get(execution.id).state.value == "failed"
