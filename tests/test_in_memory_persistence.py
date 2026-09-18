from uuid import uuid4

from app.domain.execution import Execution
from app.domain.workflow import Workflow
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


def test_workflow_repository_saves_and_gets_workflow():
    repository = InMemoryWorkflowRepository()
    workflow = Workflow.create("Pipeline", [])

    repository.save(workflow)

    assert repository.get(workflow.id) is workflow


def test_execution_repository_saves_and_gets_execution():
    repository = InMemoryExecutionRepository()
    execution = Execution.create(uuid4())

    repository.save(execution)

    assert repository.get(execution.id) is execution


def test_workflow_repository_replaces_existing_aggregate_by_id():
    repository = InMemoryWorkflowRepository()
    first = Workflow.create("Pipeline", [])
    second = Workflow(id=first.id, name="Updated", _steps=[], state=first.state)

    repository.save(first)
    repository.save(second)

    assert repository.get(first.id) is second


def test_execution_repository_replaces_existing_aggregate_by_id():
    repository = InMemoryExecutionRepository()
    first = Execution.create(uuid4())
    second = Execution(
        id=first.id,
        workflow_id=first.workflow_id,
        current_step=1,
        state=first.state,
        attempt=first.attempt,
    )

    repository.save(first)
    repository.save(second)

    assert repository.get(first.id) is second


def test_repositories_return_none_for_unknown_id():
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()

    assert workflow_repository.get(uuid4()) is None
    assert execution_repository.get(uuid4()) is None
