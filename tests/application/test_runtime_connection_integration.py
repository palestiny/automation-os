from uuid import uuid4

import pytest

from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_context import ExecutionContext
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


class FakeExecutionRepository:
    def __init__(self, execution):
        self.execution = execution
        self.saved = []

    def get(self, execution_id):
        return self.execution if execution_id == self.execution.id else None

    def save(self, execution):
        self.saved.append(execution)


class FakeWorkflowRepository:
    def __init__(self, workflow):
        self.workflow = workflow

    def get(self, workflow_id):
        return self.workflow if workflow_id == self.workflow.id else None


class FakeWorkflowVersionRepository:
    def __init__(self, version):
        self.version = version

    def get(self, version_id):
        return self.version if version_id == self.version.id else None


class FakeDispatcher:
    def __init__(self):
        self.calls = []

    def dispatch(self, capability_id, context):
        self.calls.append((capability_id, context))
        return type("Result", (), {"succeeded": True})()


def published_version():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create("publish", "youtube.publish")],
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
    return workflow, version, tenant_id


def test_runtime_preparation_failure_fails_execution_before_capability():
    workflow, version, tenant_id = published_version()
    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution_repository = FakeExecutionRepository(execution)
    dispatcher = FakeDispatcher()

    class FailingPreparer:
        def prepare(self, **kwargs):
            raise RuntimeError("connection revoked")

    executor = ExecuteWorkflowStep(
        FakeWorkflowRepository(workflow),
        execution_repository,
        dispatcher,
        type("Conditions", (), {"evaluate": lambda *_: True})(),
        FakeWorkflowVersionRepository(version),
        FailingPreparer(),
    )

    with pytest.raises(RuntimeError, match="connection revoked"):
        executor.execute(execution.id, ExecutionContext())

    assert dispatcher.calls == []
    assert execution.state is ExecutionState.FAILED
    assert execution_repository.saved[-1] is execution


def test_runtime_context_cannot_be_injected_by_caller():
    context = ExecutionContext()
    with pytest.raises(ValueError, match="Runtime-owned"):
        context.set("runtime.connections", object())


def test_runtime_preparation_runs_once_for_repeated_steps():
    workflow, version, tenant_id = published_version()
    version.add_step(WorkflowStep.create("second", "youtube.publish"))
    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution_repository = FakeExecutionRepository(execution)
    dispatcher = FakeDispatcher()

    class Preparer:
        def __init__(self):
            self.calls = 0

        def prepare(self, **kwargs):
            self.calls += 1
            kwargs["context"].set_runtime("runtime.connections", object())

    preparer = Preparer()
    executor = ExecuteWorkflowStep(
        FakeWorkflowRepository(workflow),
        execution_repository,
        dispatcher,
        type("Conditions", (), {"evaluate": lambda *_: True})(),
        FakeWorkflowVersionRepository(version),
        preparer,
    )
    context = ExecutionContext()

    executor.execute(execution.id, context)
    executor.execute(execution.id, context)

    assert preparer.calls == 1
    assert len(dispatcher.calls) == 2
