from uuid import uuid4

import pytest

from app.application.connection_runtime_composition import RuntimeConnectionPreparerFactory
from app.application.execution_context import ExecutionContext
from app.domain.connection import Connection, ConnectionRequirement
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import InMemoryConnectionRepository


class RecordingSecretProvider:
    def __init__(self):
        self.references = []

    def get_secret(self, secret_reference):
        self.references.append(secret_reference)
        return {"token": "runtime-only"}


def test_factory_binds_resolver_to_execution_tenant():
    tenant_a = uuid4()
    tenant_b = uuid4()
    repositories = {
        tenant_a: InMemoryConnectionRepository(tenant_a),
        tenant_b: InMemoryConnectionRepository(tenant_b),
    }
    connection = Connection.create(
        tenant_id=tenant_a,
        provider_id="youtube",
        reference="primary",
        authentication_type="api_key",
        secret_reference="secret/youtube/primary",
    )
    repositories[tenant_a].save(connection)

    secret_provider = RecordingSecretProvider()
    factory = RuntimeConnectionPreparerFactory(
        lambda tenant_id: repositories[tenant_id],
        secret_provider,
    )

    workflow = Workflow.create("Tenant workflow", [WorkflowStep.create("run", "test")])
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_a,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "primary"),
        ],
    )

    context = ExecutionContext()
    prepared = factory.create(tenant_a).prepare(
        workflow_version=version,
        tenant_id=tenant_a,
        context=context,
    )

    assert prepared.connections[0].connection_id == connection.id
    assert prepared.connections[0].tenant_id == tenant_a
    assert secret_provider.references == ["secret/youtube/primary"]


def test_factory_cannot_cross_tenant_connection_boundary():
    tenant_a = uuid4()
    tenant_b = uuid4()
    repositories = {
        tenant_a: InMemoryConnectionRepository(tenant_a),
        tenant_b: InMemoryConnectionRepository(tenant_b),
    }
    connection = Connection.create(
        tenant_id=tenant_a,
        provider_id="youtube",
        reference="primary",
        authentication_type="api_key",
        secret_reference="secret/youtube/primary",
    )
    repositories[tenant_a].save(connection)

    factory = RuntimeConnectionPreparerFactory(
        lambda tenant_id: repositories[tenant_id],
        RecordingSecretProvider(),
    )
    workflow = Workflow.create("Tenant workflow", [WorkflowStep.create("run", "test")])
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_b,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "primary"),
        ],
    )

    with pytest.raises(LookupError):
        factory.create(tenant_b).prepare(
            workflow_version=version,
            tenant_id=tenant_b,
            context=ExecutionContext(),
        )


def test_factory_fails_when_workflow_and_execution_tenants_differ():
    tenant_a = uuid4()
    tenant_b = uuid4()
    factory = RuntimeConnectionPreparerFactory(
        lambda tenant_id: InMemoryConnectionRepository(tenant_id),
        RecordingSecretProvider(),
    )
    workflow = Workflow.create("Tenant workflow", [WorkflowStep.create("run", "test")])
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_a,
    )

    with pytest.raises(PermissionError):
        factory.create(tenant_b).prepare(
            workflow_version=version,
            tenant_id=tenant_b,
            context=ExecutionContext(),
        )


def test_factory_uses_only_persisted_requirement_and_not_context_override():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id)
    persisted = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="persisted",
        authentication_type="api_key",
        secret_reference="secret/persisted",
    )
    override = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="override",
        authentication_type="api_key",
        secret_reference="secret/override",
    )
    repository.save(persisted)
    repository.save(override)

    factory = RuntimeConnectionPreparerFactory(
        lambda _: repository,
        RecordingSecretProvider(),
    )
    workflow = Workflow(
        id=uuid4(),
        name="Tenant workflow",
        _steps=[WorkflowStep.create("run", "test")],
        state=__import__("app.domain.workflow", fromlist=["WorkflowState"]).WorkflowState.DRAFT,
        tenant_id=tenant_id,
    )
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "persisted"),
        ],
    )

    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.set("runtime.connections", "caller override")

    prepared = factory.create(tenant_id).prepare(
        workflow_version=version,
        tenant_id=tenant_id,
        context=context,
    )

    assert prepared.connections[0].reference == "persisted"
    assert prepared.connections[0].secret_material == {"token": "runtime-only"}


def test_execute_workflow_step_builds_runtime_preparer_from_execution_tenant():
    from app.application.capability_dispatcher import CapabilityDispatcher
    from app.application.capability_registry import CapabilityRegistry
    from app.application.condition_evaluator import ConditionEvaluator
    from app.application.execute_workflow_step import ExecuteWorkflowStep
    from app.application.capability_result import CapabilityResult
    from app.domain.execution import Execution
    from app.infrastructure.persistence.in_memory import (
        InMemoryExecutionRepository,
        InMemoryWorkflowRepository,
        InMemoryWorkflowVersionRepository,
    )

    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id)
    repository.save(
        Connection.create(
            tenant_id=tenant_id,
            provider_id="youtube",
            reference="primary",
            authentication_type="api_key",
            secret_reference="secret/youtube/primary",
        )
    )

    workflow = Workflow.create("Tenant workflow", [WorkflowStep.create("run", "test")])
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[
            ConnectionRequirement.create("youtube", "primary"),
        ],
    )
    version.publish()

    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()

    workflows = InMemoryWorkflowRepository(tenant_id)
    versions = InMemoryWorkflowVersionRepository(tenant_id)
    executions = InMemoryExecutionRepository(tenant_id)
    workflows.save(workflow)
    versions.save(version)
    executions.save(execution)

    class RuntimeAwareCapability:
        def execute(self, context):
            prepared = context.get_runtime_connections()
            assert prepared.connections[0].reference == "primary"
            assert prepared.connections[0].secret_material == {"token": "runtime-only"}
            return CapabilityResult.success()

    registry = CapabilityRegistry()
    registry.register("test", RuntimeAwareCapability())
    use_case = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
        versions,
        runtime_connection_preparer_factory=RuntimeConnectionPreparerFactory(
            lambda requested_tenant: repository,
            RecordingSecretProvider(),
        ),
    )

    result = use_case.execute(execution.id, ExecutionContext())

    assert result.processed is True
    assert execution.state.value == "completed"
