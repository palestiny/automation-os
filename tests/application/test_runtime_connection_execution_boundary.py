from uuid import uuid4

import pytest

from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.application.connection_runtime_resolution import ResolveRuntimeConnection
from app.application.connection_resolver import ConnectionNotFoundError
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Condition, Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


class MemoryExecutionRepository:
    def __init__(self, execution):
        self.execution = execution

    def get(self, execution_id):
        return self.execution

    def save(self, execution):
        self.execution = execution


class MemoryWorkflowRepository:
    def __init__(self, workflow):
        self.workflow = workflow

    def get(self, workflow_id):
        return self.workflow


class MemoryVersionRepository:
    def __init__(self, version):
        self.version = version

    def get(self, version_id):
        return self.version


class ExplodingDispatcher:
    def __init__(self):
        self.calls = 0

    def dispatch(self, capability_id, context):
        self.calls += 1
        return CapabilityResult.success()


def build_case(condition=None):
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish", condition=condition)],
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
    version.publish()
    execution = Execution.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()
    return tenant_id, workflow, version, execution


def test_missing_runtime_connection_fails_before_capability_invocation():
    tenant_id, workflow, version, execution = build_case()

    class MissingResolver:
        def resolve(self, **kwargs):
            raise ConnectionNotFoundError("missing")

    preparer = PrepareWorkflowRuntimeConnections(
        ResolveRuntimeConnection(
            MissingResolver(),
            lambda: None,
        )
    )
    dispatcher = ExplodingDispatcher()

    executor = ExecuteWorkflowStep(
        MemoryWorkflowRepository(workflow),
        MemoryExecutionRepository(execution),
        dispatcher,
        ConditionEvaluator(),
        MemoryVersionRepository(version),
        preparer,
    )

    with pytest.raises(ConnectionNotFoundError):
        executor.execute(execution.id, ExecutionContext())

    assert dispatcher.calls == 0
    assert execution.state is ExecutionState.FAILED


def test_caller_cannot_override_reserved_runtime_connections():
    context = ExecutionContext()

    with pytest.raises(ValueError):
        context.set("runtime.connections", object())


def test_false_condition_does_not_resolve_runtime_connection():
    condition = Condition.create("enabled", "equals", True)
    tenant_id, workflow, version, execution = build_case(condition)

    calls = []

    class RecordingPreparer:
        def prepare(self, **kwargs):
            calls.append(kwargs)

    dispatcher = ExplodingDispatcher()
    executor = ExecuteWorkflowStep(
        MemoryWorkflowRepository(workflow),
        MemoryExecutionRepository(execution),
        dispatcher,
        ConditionEvaluator(),
        MemoryVersionRepository(version),
        RecordingPreparer(),
    )
    context = ExecutionContext()
    context.set("enabled", False)

    executor.execute(execution.id, context)

    assert calls == []
    assert dispatcher.calls == 0
