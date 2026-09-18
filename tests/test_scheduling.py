from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.scheduling import (
    FixedClock,
    Schedule,
    ScheduledExecutionRequest,
)


def test_scheduled_execution_request_is_immutable():
    request = ScheduledExecutionRequest.create(
        workflow_id=uuid4(),
        scheduled_at=datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(AttributeError):
        request.workflow_id = uuid4()


def test_schedule_is_not_due_before_scheduled_time():
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    schedule = Schedule(
        ScheduledExecutionRequest.create(uuid4(), scheduled_at)
    )

    assert (
        schedule.is_due(
            FixedClock(datetime(2026, 9, 18, 19, 59, tzinfo=timezone.utc))
        )
        is False
    )


def test_schedule_is_due_at_scheduled_time():
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    schedule = Schedule(
        ScheduledExecutionRequest.create(uuid4(), scheduled_at)
    )

    assert schedule.is_due(FixedClock(scheduled_at)) is True


def test_schedule_is_due_after_scheduled_time():
    scheduled_at = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    schedule = Schedule(
        ScheduledExecutionRequest.create(uuid4(), scheduled_at)
    )

    assert (
        schedule.is_due(
            FixedClock(datetime(2026, 9, 18, 20, 1, tzinfo=timezone.utc))
        )
        is True
    )


def test_scheduled_execution_request_requires_uuid():
    with pytest.raises(
        ValueError,
        match="workflow_id must be a UUID",
    ):
        ScheduledExecutionRequest.create(
            "workflow-id",
            datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc),
        )


def test_scheduled_execution_request_requires_datetime():
    with pytest.raises(
        ValueError,
        match="scheduled_at must be a datetime",
    ):
        ScheduledExecutionRequest.create(uuid4(), "tomorrow")
