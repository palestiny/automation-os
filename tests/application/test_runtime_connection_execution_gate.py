from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self):
        self.calls = 0

    def execute(self, context):
        self.calls += 1
        return CapabilityResult.success()


class FailingPreparation:
    def __init__(self, error):
        self.error = error
        self.calls = 0

    def prepare(self, **kwargs):
        self.calls += 1
        raise self.error


def test_version_inherits_workflow_tenant_when_not_explicitly_overridden():
    tenant_id = uuid4()
    workflow = Workflow.create(
        "Tenant workflow",
        [WorkflowStep.create("Step", "test")],
        tenant_id=tenant_id,
    )

    version = WorkflowVersion.create_from_workflow(workflow, 1)

    assert version.tenant_id == tenant_id


def test_runtime_connection_failure_fails_execution_before_capability_invocation():
    tenant_id = uuid4()
    workflow = Workflow.create(
        "Connected workflow",
        [WorkflowStep.create("Step", "test")],
        tenant_id=tenant_id,
    )
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "youtube.primary")
        ],
    )
    version.publish()

    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    executions.save(execution)

    capability = RecordingCapability()
    registry = CapabilityRegistry()
    registry.register("test", capability)

    preparation_error = RuntimeError("connection unavailable")
    preparer = FailingPreparation(preparation_error)

    use_case = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
        workflow_version_repository=type(
            "Versions",
            (),
            {"get": lambda self, version_id: version},
        )(),
        runtime_connection_preparer=preparer,
    )

    with pytest.raises(RuntimeError, match="connection unavailable"):
        use_case.execute(execution.id, ExecutionContext())

    assert preparer.calls == 1
    assert capability.calls == 0
    assert execution.current_step == 0
    assert execution.state.name == "FAILED"
