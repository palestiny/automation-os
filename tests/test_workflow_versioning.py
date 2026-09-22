from uuid import uuid4

import pytest

from app.application.create_workflow_version import CreateWorkflowVersion
from app.application.publish_workflow_version import PublishWorkflowVersion
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


def published_workflow() -> Workflow:
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow.publish()
    return workflow


def test_create_workflow_version_is_draft_and_has_stable_identity():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    created = CreateWorkflowVersion(workflows, versions).execute(workflow.id)

    assert created.workflow_id == workflow.id
    assert created.version_number == 1
    assert created.state is WorkflowState.DRAFT
    assert created.steps == workflow.steps
    assert versions.get(created.id) == created


def test_published_workflow_version_cannot_be_mutated():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)
    version = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    version.publish()
    versions.save(version)

    with pytest.raises(ValueError, match="DRAFT"):
        version.add_step(WorkflowStep.create("Step 2", "test"))

    assert versions.get(version.id).steps == version.steps


def test_new_version_clones_latest_published_version_with_incremented_number():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    first = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    first.publish()
    versions.save(first)

    second = CreateWorkflowVersion(workflows, versions).execute(workflow.id)

    assert second.version_number == 2
    assert second.id != first.id
    assert second.state is WorkflowState.DRAFT
    assert second.steps == first.steps


def test_publish_workflow_version_requires_existing_draft():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    version = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    result = PublishWorkflowVersion(versions).execute(version.id)

    assert result.state is WorkflowState.PUBLISHED
    assert versions.get(version.id).state is WorkflowState.PUBLISHED


def test_start_workflow_execution_materializes_legacy_version_and_persists_it():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    result = StartWorkflowExecution(
        workflows,
        executions,
        workflow_version_repository=versions,
    ).execute(workflow.id)

    assert result.state is ExecutionState.RUNNING
    assert result.workflow_version_id is not None
    version = versions.get(result.workflow_version_id)
    assert version is not None
    assert version.workflow_id == workflow.id
    assert version.version_number == 1
    assert version.state is WorkflowState.PUBLISHED


def test_start_workflow_execution_uses_latest_published_version_by_default():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    first = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    first.publish()
    versions.save(first)
    second = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    second.add_step(WorkflowStep.create("Step 2", "test"))
    second.publish()
    versions.save(second)

    result = StartWorkflowExecution(
        workflows,
        executions,
        workflow_version_repository=versions,
    ).execute(workflow.id)

    assert result.workflow_version_id == second.id


def test_start_workflow_execution_can_select_explicit_published_version():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    first = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    first.publish()
    versions.save(first)
    second = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    second.publish()
    versions.save(second)

    result = StartWorkflowExecution(
        workflows,
        executions,
        workflow_version_repository=versions,
    ).execute(workflow.id, workflow_version_id=first.id)

    assert result.workflow_version_id == first.id



def test_create_workflow_version_rejects_draft_workflow():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = Workflow.create(
        "Draft",
        [WorkflowStep.create("Step 1", "test")],
    )
    workflows.save(workflow)

    with pytest.raises(ValueError, match="published"):
        CreateWorkflowVersion(workflows, versions).execute(workflow.id)



def test_workflow_version_repository_isolates_tenants_in_memory():
    workflows = InMemoryWorkflowRepository()
    tenant_a = uuid4()
    tenant_b = uuid4()
    workflow = published_workflow()
    workflows.save(workflow)

    versions_a = InMemoryWorkflowVersionRepository(tenant_id=tenant_a)
    version = CreateWorkflowVersion(
        workflows, versions_a, tenant_id=tenant_a
    ).execute(workflow.id)
    versions_a.save(version)

    versions_b = InMemoryWorkflowVersionRepository(tenant_id=tenant_b)
    assert versions_b.get(version.id) is None
    assert versions_b.all() == ()


def test_workflow_version_rejects_cross_tenant_save_in_memory():
    workflow = published_workflow()
    version = WorkflowVersion.create_from_workflow(
        workflow, 1, tenant_id=uuid4()
    )
    repository = InMemoryWorkflowVersionRepository(tenant_id=uuid4())

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(version)
