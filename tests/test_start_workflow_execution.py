from uuid import uuid4

import pytest

from app.application.create_workflow_version import CreateWorkflowVersion
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


def test_start_workflow_execution_persists_running_execution():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    result = StartWorkflowExecution(
        workflows, executions, workflow_version_repository=versions
    ).execute(workflow.id)

    assert result.state is ExecutionState.RUNNING
    assert result.workflow_id == workflow.id
    assert result.workflow_version_id is not None
    assert executions.get(result.id) is result


def test_start_workflow_execution_rejects_missing_workflow():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()

    with pytest.raises(ValueError, match="Workflow not found"):
        StartWorkflowExecution(workflows, executions).execute(uuid4())


def test_start_workflow_execution_rejects_draft_workflow_without_persisting_execution():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    workflows.save(workflow)

    with pytest.raises(ValueError, match="published"):
        StartWorkflowExecution(workflows, executions).execute(workflow.id)

    assert executions.all() == ()


def test_start_workflow_execution_rejects_draft_explicit_version_without_persisting_execution():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    draft_version = CreateWorkflowVersion(workflows, versions).execute(workflow.id)

    with pytest.raises(ValueError, match="published workflow versions"):
        StartWorkflowExecution(
            workflows,
            executions,
            workflow_version_repository=versions,
        ).execute(workflow.id, workflow_version_id=draft_version.id)

    assert executions.all() == ()


def test_start_workflow_execution_rejects_version_from_different_workflow_without_persisting_execution():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflow = published_workflow()
    other_workflow = published_workflow()
    workflows.save(workflow)
    workflows.save(other_workflow)

    other_version = CreateWorkflowVersion(workflows, versions).execute(other_workflow.id)
    other_version.publish()
    versions.save(other_version)

    with pytest.raises(ValueError, match="different workflow"):
        StartWorkflowExecution(
            workflows,
            executions,
            workflow_version_repository=versions,
        ).execute(workflow.id, workflow_version_id=other_version.id)

    assert executions.all() == ()
