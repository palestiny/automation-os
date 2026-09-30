from uuid import uuid4

import pytest

from app.application.connection_runtime_resolution import ResolvedConnection
from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import (
    PreparedRuntimeConnections,
    PrepareWorkflowRuntimeConnections,
)
from app.domain.connection import ConnectionRequirement
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def test_runtime_preparation_uses_persisted_requirements_only():
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
            ConnectionRequirement.create("youtube", "youtube.primary"),
        ],
    )
    calls = []

    class FakeResolver:
        def resolve(self, **kwargs):
            calls.append(kwargs)
            return ResolvedConnection(
                connection_id=uuid4(),
                tenant_id=tenant_id,
                provider_id=kwargs["provider_id"],
                reference=kwargs["reference"],
                authentication_type="api_key",
                secret_material=object(),
            )

    context = ExecutionContext()
    prepared = PrepareWorkflowRuntimeConnections(FakeResolver()).prepare(
        workflow_version=version,
        tenant_id=tenant_id,
        context=context,
    )

    assert calls == [
        {
            "tenant_id": tenant_id,
            "provider_id": "youtube",
            "reference": "youtube.primary",
        }
    ]
    assert context.get_runtime_connections() is prepared
    assert prepared.connections[0].reference == "youtube.primary"


def test_runtime_preparation_rejects_cross_tenant_version():
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
    )
    with pytest.raises(PermissionError):
        PrepareWorkflowRuntimeConnections(object()).prepare(
            workflow_version=version,
            tenant_id=uuid4(),
            context=ExecutionContext(),
        )


def test_prepared_runtime_connections_repr_does_not_expose_secret():
    tenant_id = uuid4()
    secret = "super-secret-value"
    prepared = PreparedRuntimeConnections(
        (
            ResolvedConnection(
                connection_id=uuid4(),
                tenant_id=tenant_id,
                provider_id="youtube",
                reference="youtube.primary",
                authentication_type="api_key",
                secret_material=secret,
            ),
        )
    )

    assert secret not in repr(prepared)
    assert "secret_material" not in repr(prepared)


def test_preparation_overwrites_any_preexisting_runtime_connection_value():
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
            ConnectionRequirement.create("youtube", "youtube.persisted"),
        ],
    )

    class FakeResolver:
        def resolve(self, **kwargs):
            return ResolvedConnection(
                connection_id=uuid4(),
                tenant_id=tenant_id,
                provider_id=kwargs["provider_id"],
                reference=kwargs["reference"],
                authentication_type="api_key",
                secret_material="resolved-secret",
            )

    context = ExecutionContext()
    context.set("runtime.connections", "caller-controlled-value")

    prepared = PrepareWorkflowRuntimeConnections(FakeResolver()).prepare(
        workflow_version=version,
        tenant_id=tenant_id,
        context=context,
    )

    assert context.get("runtime.connections") is prepared
    assert prepared.connections[0].reference == "youtube.persisted"
