from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.start_workflow_execution import StartWorkflowExecution
from app.core.execution_dependencies import (
    execution_history_repository,
    execution_idempotency_repository,
    execution_repository,
    workflow_repository,
)
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    EventRecordingExecutionRepository,
    InMemoryExecutionHistoryRepository,
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
)
from app.main import app


client = TestClient(app)


def published_workflow(name: str = "Pipeline") -> Workflow:
    workflow = Workflow.create(
        name,
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow.publish()
    return workflow


def test_start_workflow_execution_is_idempotent_for_same_key():
    workflows = InMemoryExecutionRepository()
    workflow_repository = __import__(
        "app.infrastructure.persistence.in_memory",
        fromlist=["InMemoryWorkflowRepository"],
    ).InMemoryWorkflowRepository()
    workflow = published_workflow()
    workflow_repository.save(workflow)

    idempotency = InMemoryExecutionIdempotencyRepository()
    executions = workflows
    start = StartWorkflowExecution(
        workflow_repository,
        executions,
        idempotency_repository=idempotency,
    )

    first = start.execute(workflow.id, idempotency_key="request-1")
    second = start.execute(workflow.id, idempotency_key="request-1")

    assert second is first
    assert len(executions.all()) == 1
    assert first.state is ExecutionState.RUNNING


def test_start_workflow_execution_rejects_idempotency_key_reuse_for_other_workflow():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    first_workflow = published_workflow("First")
    second_workflow = published_workflow("Second")
    workflows.save(first_workflow)
    workflows.save(second_workflow)

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
    )

    start.execute(first_workflow.id, idempotency_key="request-1")

    with pytest.raises(ValueError, match="Idempotency key"):
        start.execute(second_workflow.id, idempotency_key="request-1")

    assert len(executions.all()) == 1


def test_execution_history_records_structured_start_event():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    inner_executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    executions = EventRecordingExecutionRepository(inner_executions, history)
    workflow = published_workflow()
    workflows.save(workflow)

    result = StartWorkflowExecution(workflows, executions).execute(workflow.id)

    entries = history.list(result.id)

    assert len(entries) == 1
    assert entries[0].event_type == "execution.started"
    assert entries[0].execution_id == result.id
    assert entries[0].workflow_id == workflow.id
    assert entries[0].state is ExecutionState.RUNNING
    assert entries[0].attempt == 1
    assert entries[0].sequence == 1


def test_execution_history_is_append_only_when_execution_is_saved_again():
    from app.domain.execution import Execution

    history = InMemoryExecutionHistoryRepository()
    inner_executions = InMemoryExecutionRepository()
    executions = EventRecordingExecutionRepository(inner_executions, history)
    execution = Execution.create(uuid4())

    execution.start()
    executions.save(execution)
    executions.save(execution)

    entries = history.list(execution.id)

    assert len(entries) == 1
    assert entries[0].sequence == 1


def test_api_replays_same_execution_for_duplicate_idempotency_key():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflow = published_workflow("API Idempotent Pipeline")
    workflow_repository.save(workflow)

    key = f"api-{uuid4()}"
    first = client.post(
        f"/executions/workflows/{workflow.id}",
        headers={"Idempotency-Key": key},
    )
    second = client.post(
        f"/executions/workflows/{workflow.id}",
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["execution_id"] == first.json()["execution_id"]


def test_api_rejects_idempotency_key_reuse_for_other_workflow():
    first_workflow = published_workflow("API First")
    second_workflow = published_workflow("API Second")
    workflow_repository.save(first_workflow)
    workflow_repository.save(second_workflow)

    key = f"api-conflict-{uuid4()}"
    first = client.post(
        f"/executions/workflows/{first_workflow.id}",
        headers={"Idempotency-Key": key},
    )
    second = client.post(
        f"/executions/workflows/{second_workflow.id}",
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 200
    assert second.status_code == 409
