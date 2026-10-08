from uuid import uuid4

import pytest

from app.application.capability_result import CapabilityResult
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import (
    PrepareWorkflowRuntimeConnections,
)
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
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
        return CapabilityResult.success()


class AlwaysRunConditions:
    def evaluate(self, condition, context):
        return True


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


def test_runtime_preparation_runs_before_capability_without_caller_override():
    workflow, version, tenant_id = published_version()
    execution = Execution.create(workflow.id, workflow_version_id=version.id, tenant_id=tenant_id)
    execution.start()
    execution_repository = FakeExecutionRepository(execution)
    dispatcher = FakeDispatcher()

    class Resolver:
        def resolve(self, *, tenant_id, provider_id, reference):
            assert tenant_id == version.tenant_id
            assert provider_id == "youtube"
            assert reference == "youtube.primary"
            from app.application.connection_runtime_resolution import ResolvedConnection
            return ResolvedConnection(
                connection_id=uuid4(),
                tenant_id=tenant_id,
                provider_id=provider_id,
                reference=reference,
                authentication_type="api_key",
                secret_material="test-secret",
            )

    preparer = PrepareWorkflowRuntimeConnections(Resolver())
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.set("runtime.connections", "caller-controlled")

    ExecuteWorkflowStep(
        FakeWorkflowRepository(workflow),
        execution_repository,
        dispatcher,
        AlwaysRunConditions(),
        FakeWorkflowVersionRepository(version),
        preparer,
    ).execute(execution.id, context)

    assert len(dispatcher.calls) == 1
    assert len(dispatcher.calls[0][1].get_runtime_connections().connections) == 1


def test_missing_runtime_preparation_fails_before_capability_invocation():
    workflow, version, _ = published_version()
    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution_repository = FakeExecutionRepository(execution)
    dispatcher = FakeDispatcher()

    with pytest.raises(RuntimeError, match="runtime connection preparation"):
        ExecuteWorkflowStep(
            FakeWorkflowRepository(workflow),
            execution_repository,
            dispatcher,
            AlwaysRunConditions(),
            FakeWorkflowVersionRepository(version),
        ).execute(execution.id, ExecutionContext())

    assert dispatcher.calls == []
    assert execution.state is ExecutionState.FAILED
