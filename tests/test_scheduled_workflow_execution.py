from datetime import datetime, timezone
from uuid import uuid4

from app.application.scheduled_workflow_execution import StartDueWorkflowExecution
from app.application.scheduling import FixedClock, ScheduledExecutionRequest


class FakeStartWorkflowExecution:
    def __init__(self) -> None:
        self.workflow_ids: list = []

    def execute(self, workflow_id):
        self.workflow_ids.append(workflow_id)
        return object()


def test_not_due_request_does_not_start_workflow():
    workflow_id = uuid4()
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    starter = FakeStartWorkflowExecution()
    use_case = StartDueWorkflowExecution(
        start_workflow_execution=starter,
        clock=FixedClock(
            datetime(2026, 9, 18, 19, 59, tzinfo=timezone.utc)
        ),
    )

    result = use_case.execute(
        ScheduledExecutionRequest.create(workflow_id, scheduled_at)
    )

    assert result is None
    assert starter.workflow_ids == []


def test_due_request_delegates_to_start_workflow_execution():
    workflow_id = uuid4()
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    starter = FakeStartWorkflowExecution()
    use_case = StartDueWorkflowExecution(
        start_workflow_execution=starter,
        clock=FixedClock(scheduled_at),
    )

    result = use_case.execute(
        ScheduledExecutionRequest.create(workflow_id, scheduled_at)
    )

    assert result is not None
    assert starter.workflow_ids == [workflow_id]


def test_due_request_after_scheduled_time_delegates_to_start_workflow_execution():
    workflow_id = uuid4()
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    starter = FakeStartWorkflowExecution()
    use_case = StartDueWorkflowExecution(
        start_workflow_execution=starter,
        clock=FixedClock(
            datetime(2026, 9, 18, 20, 1, tzinfo=timezone.utc)
        ),
    )

    use_case.execute(
        ScheduledExecutionRequest.create(workflow_id, scheduled_at)
    )

    assert starter.workflow_ids == [workflow_id]
