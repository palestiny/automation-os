from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.scheduling import FixedClock
from app.application.scheduling_progress_composition import SchedulingProgressComposition
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow
from tests.test_repository_contracts import InMemoryExecutionRepository, InMemoryWorkflowRepository


def test_due_schedule_starts_execution_and_progress_reads_same_execution():
    workflow = Workflow.create("Scheduled content workflow", [])
    workflow.publish()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    composition = SchedulingProgressComposition(
        workflows,
        executions,
        FixedClock(scheduled_at),
    )

    request = composition.schedule(workflow.id, scheduled_at)
    execution = composition.start_if_due(request)

    assert execution is not None
    assert execution.state == ExecutionState.RUNNING

    progress = composition.get_progress(execution.id)

    assert progress.execution_id == execution.id
    assert progress.workflow_id == workflow.id
    assert progress.state == ExecutionState.RUNNING
    assert progress.current_step == 0
    assert progress.attempt == 1


def test_not_due_schedule_does_not_create_execution():
    workflow = Workflow.create("Scheduled content workflow", [])
    workflow.publish()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    composition = SchedulingProgressComposition(
        workflows,
        executions,
        FixedClock(datetime(2026, 9, 18, 19, 59, tzinfo=timezone.utc)),
    )

    request = composition.schedule(workflow.id, scheduled_at)

    assert composition.start_if_due(request) is None
    assert executions.items == {}


def test_schedule_requires_published_workflow_when_due():
    workflow = Workflow.create("Draft workflow", [])
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    composition = SchedulingProgressComposition(
        workflows,
        executions,
        FixedClock(scheduled_at),
    )

    request = composition.schedule(workflow.id, scheduled_at)

    with pytest.raises(ValueError, match="published"):
        composition.start_if_due(request)

    assert executions.items == {}
