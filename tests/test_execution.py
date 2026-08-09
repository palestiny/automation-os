from uuid import uuid4

import pytest

from app.domain.execution import Execution, ExecutionState


def test_execution_starts_successfully():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    assert execution.state == ExecutionState.RUNNING
    assert execution.started_at is not None


def test_execution_cannot_start_twice():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    with pytest.raises(ValueError):
        execution.start()