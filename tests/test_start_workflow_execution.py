from uuid import uuid4

import pytest

from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
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
    workflow = published_workflow()
    workflows.save(workflow)

    result = StartWorkflowExecution(workflows, executions).execute(workflow.id)

    assert result.state is ExecutionState.RUNNING
    assert result.workflow_id == workflow.id
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

    assert executions.get(uuid4()) is None
