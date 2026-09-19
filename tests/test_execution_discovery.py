from uuid import uuid4

from app.application.execution_discovery import DiscoverExecutions
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def make_execution(workflow_id=None):
    return Execution.create(workflow_id or uuid4())


def test_discover_executions_returns_progress_for_all():
    repo = InMemoryExecutionRepository()
    first = make_execution()
    second = make_execution()
    repo.save(first)
    repo.save(second)

    result = DiscoverExecutions(repo).execute()

    assert tuple(item.execution_id for item in result) == (first.id, second.id)


def test_discover_executions_filters_by_workflow():
    repo = InMemoryExecutionRepository()
    workflow_id = uuid4()
    matching = make_execution(workflow_id)
    other = make_execution()
    repo.save(matching)
    repo.save(other)

    result = DiscoverExecutions(repo).execute(workflow_id=workflow_id)

    assert [item.execution_id for item in result] == [matching.id]


def test_discover_executions_filters_by_state():
    repo = InMemoryExecutionRepository()
    running = make_execution()
    running.start()
    created = make_execution()
    repo.save(running)
    repo.save(created)

    result = DiscoverExecutions(repo).execute(state=ExecutionState.RUNNING)

    assert [item.execution_id for item in result] == [running.id]


def test_discover_executions_returns_empty_for_no_match():
    repo = InMemoryExecutionRepository()
    repo.save(make_execution())

    result = DiscoverExecutions(repo).execute(workflow_id=uuid4())

    assert result == ()
