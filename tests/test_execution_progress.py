from uuid import uuid4

import pytest

from app.application.execution_progress import (
    ExecutionProgress,
    ExecutionProgressNotFoundError,
    GetExecutionProgress,
)
from app.domain.execution import Execution, ExecutionState
def test_progress_projects_execution_state_without_mutating_execution():
    workflow_id = uuid4()
    execution = Execution.create(workflow_id)
    execution.start()

    repository = InMemoryExecutionRepository()
    repository.save(execution)

    progress = GetExecutionProgress(repository).execute(execution.id)

    assert isinstance(progress, ExecutionProgress)
    assert progress.execution_id == execution.id
    assert progress.workflow_id == workflow_id
    assert progress.current_step == execution.current_step
    assert progress.state == ExecutionState.RUNNING
    assert progress.attempt == 1
    assert progress.started_at == execution.started_at
    assert progress.finished_at is None


def test_progress_reflects_completed_execution():
    execution = Execution.create(uuid4())
    execution.start()
    execution.complete_step()
    execution.complete()

    repository = InMemoryExecutionRepository()
    repository.save(execution)

    progress = GetExecutionProgress(repository).execute(execution.id)

    assert progress.current_step == 1
    assert progress.state == ExecutionState.COMPLETED
    assert progress.finished_at == execution.finished_at


def test_progress_is_immutable():
    execution = Execution.create(uuid4())
    repository = InMemoryExecutionRepository()
    repository.save(execution)

    progress = GetExecutionProgress(repository).execute(execution.id)

    with pytest.raises(AttributeError):
        progress.current_step = 10


def test_progress_for_unknown_execution_is_explicit():
    repository = InMemoryExecutionRepository()

    with pytest.raises(
        ExecutionProgressNotFoundError,
        match="Execution not found",
    ):
        GetExecutionProgress(repository).execute(uuid4())
