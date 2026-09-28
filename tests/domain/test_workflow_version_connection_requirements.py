from uuid import uuid4

import pytest

from app.domain.connection import ConnectionRequirement
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def test_connection_requirement_is_provider_bound_and_secret_free():
    requirement = ConnectionRequirement.create(
        provider_id="youtube",
        reference="youtube.primary",
    )
    assert requirement.provider_id == "youtube"
    assert requirement.reference == "youtube.primary"
    assert "secret" not in repr(requirement).lower()


def test_connection_requirement_rejects_empty_values():
    with pytest.raises(ValueError):
        ConnectionRequirement.create(provider_id="", reference="youtube.primary")
    with pytest.raises(ValueError):
        ConnectionRequirement.create(provider_id="youtube", reference="")


def test_workflow_version_carries_connection_requirements_into_published_definition():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="Publish video",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    requirement = ConnectionRequirement.create("youtube", "youtube.primary")
    version = WorkflowVersion.create_from_workflow(
        workflow,
        version_number=1,
        tenant_id=tenant_id,
        connection_requirements=[requirement],
    )

    assert version.connection_requirements == (requirement,)
    version.publish()
    assert version.connection_requirements == (requirement,)


def test_cloning_published_version_preserves_connection_requirements():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="Publish video",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    requirement = ConnectionRequirement.create("youtube", "youtube.primary")
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[requirement],
    )
    version.publish()

    clone = WorkflowVersion.create_from_version(
        version,
        2,
        tenant_id=tenant_id,
    )

    assert clone.connection_requirements == (requirement,)
    assert clone.state.value == "draft"


def test_workflow_version_rejects_duplicate_connection_requirements():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="Publish video",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    requirement = ConnectionRequirement.create("youtube", "youtube.primary")

    with pytest.raises(ValueError, match="unique"):
        WorkflowVersion.create_from_workflow(
            workflow,
            1,
            tenant_id=tenant_id,
            connection_requirements=[requirement, requirement],
        )
