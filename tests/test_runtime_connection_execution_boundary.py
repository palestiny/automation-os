from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Condition, Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


class RecordingCapability:
    def __init__(self):
        self.calls = 0

    def execute(self, context):
        self.calls += 1
        return CapabilityResult.success()


def build_use_case(workflow, version, execution, preparer, capability):
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    versions.save(version)
    executions.save(execution)
    registry = CapabilityRegistry()
    registry.register("test", capability)
    return ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
        versions,
        preparer,
    )


def make_version(tenant_id, condition=None):
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Publish", "test", condition)],
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
    return workflow, version


def test_runtime_connection_failure_prevents_capability_invocation():
    tenant_id = uuid4()
    workflow, version = make_version(tenant_id)
    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()
    capability = RecordingCapability()

    class FailingPreparer:
        def prepare(self, **kwargs):
            raise RuntimeError("Protected secret resolution failed")

    use_case = build_use_case(
        workflow, version, execution, FailingPreparer(), capability
    )

    with pytest.raises(RuntimeError, match="Protected secret resolution failed"):
        use_case.execute(execution.id, ExecutionContext())

    assert capability.calls == 0
    assert execution.state is ExecutionState.FAILED
    assert execution.current_step == 0


def test_false_condition_does_not_resolve_runtime_connection():
    tenant_id = uuid4()
    workflow, version = make_version(
        tenant_id,
        Condition.create("enabled", "equals", True),
    )
    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()
    capability = RecordingCapability()
    calls = []

    class RecordingPreparer:
        def prepare(self, **kwargs):
            calls.append(kwargs)

    use_case = build_use_case(
        workflow, version, execution, RecordingPreparer(), capability
    )
    context = ExecutionContext()
    context.set("enabled", False)

    use_case.execute(execution.id, context)

    assert calls == []
    assert capability.calls == 0
