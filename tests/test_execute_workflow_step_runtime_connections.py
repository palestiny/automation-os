from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.connection_runtime_resolution import ResolvedConnection
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.domain.connection import ConnectionRequirement
from app.domain.execution import Execution
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


class RecordingCapability:
    def __init__(self):
        self.calls = 0
        self.runtime_connections = None

    def execute(self, context):
        self.calls += 1
        self.runtime_connections = context.get_runtime_connections()
        return CapabilityResult.success()


def build_runtime_step(version, execution, resolver, capability):
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(
        Workflow.create(
            "Logical workflow",
            [WorkflowStep.create("Logical", "test")],
            tenant_id=version.tenant_id,
        )
    )
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
        PrepareWorkflowRuntimeConnections(resolver),
    )


def test_runtime_connection_is_prepared_before_capability_invocation():
    tenant_id = uuid4()
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Logical", "test")],
        tenant_id=tenant_id,
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "youtube.persisted"),
        ],
    )
    version.publish()
    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()

    class FakeResolver:
        def resolve(self, **kwargs):
            assert kwargs == {
                "tenant_id": tenant_id,
                "provider_id": "youtube",
                "reference": "youtube.persisted",
            }
            return ResolvedConnection(
                connection_id=uuid4(),
                tenant_id=tenant_id,
                provider_id="youtube",
                reference="youtube.persisted",
                authentication_type="api_key",
                secret_material="runtime-secret",
            )

    capability = RecordingCapability()
    executor = build_runtime_step(version, execution, FakeResolver(), capability)

    executor.execute(execution.id, ExecutionContext())

    assert capability.calls == 1
    assert capability.runtime_connections is not None
    assert capability.runtime_connections.connections[0].reference == "youtube.persisted"
    assert execution.state is ExecutionState.COMPLETED


def test_connection_resolution_failure_fails_execution_before_capability():
    tenant_id = uuid4()
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Logical", "test")],
        tenant_id=tenant_id,
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "youtube.persisted"),
        ],
    )
    version.publish()
    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()

    class FailingResolver:
        def resolve(self, **kwargs):
            raise RuntimeError("connection unavailable")

    capability = RecordingCapability()
    executor = build_runtime_step(version, execution, FailingResolver(), capability)

    with pytest.raises(RuntimeError, match="connection unavailable"):
        executor.execute(execution.id, ExecutionContext())

    assert capability.calls == 0
    assert execution.state is ExecutionState.FAILED
    assert execution.current_step == 0
