from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.external_event_intake import ExternalEventIntake
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.event import Event
from app.domain.execution import Execution
from app.domain.external_event import ExternalEvent
from app.domain.workflow import Workflow, WorkflowStep


class FakeStart:
    def __init__(self):
        self.calls = []

    def execute(self, workflow_id, *, idempotency_key=None):
        self.calls.append((workflow_id, idempotency_key))
        return Execution.create(workflow_id)


class FakeWorkflowRepository:
    def __init__(self, workflows):
        self._workflows = workflows

    def all(self):
        return tuple(self._workflows)


def workflow(event_type, *, published=True):
    w = Workflow.create(
        name=f"workflow-{event_type}",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        triggers=[event_type],
    )
    if published:
        w.publish()
    return w


def test_external_event_validates_and_normalizes():
    event = ExternalEvent(
        source="github",
        event_type="push",
        payload={"repository": "automation-os"},
        event_id="evt-1",
    )

    assert event.to_event() == Event.create("push")
    assert event.deduplication_key == "external:github:evt-1"
    assert event.payload == {"repository": "automation-os"}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source": "", "event_type": "push"},
        {"source": "github", "event_type": ""},
        {"source": "github", "event_type": "push", "event_id": ""},
    ],
)
def test_external_event_rejects_invalid_identity(kwargs):
    with pytest.raises(ValueError):
        ExternalEvent(payload={}, **kwargs)


def test_intake_delegates_through_trigger_invocation_and_uses_external_id():
    matched = workflow("push")
    draft = workflow("push", published=False)
    start = FakeStart()
    intake = ExternalEventIntake(
        FakeWorkflowRepository([matched, draft]),
        start,
    )

    executions = intake.accept(
        ExternalEvent(
            source="github",
            event_type="push",
            payload={"x": 1},
            event_id="evt-42",
        )
    )

    assert [execution.workflow_id for execution in executions] == [matched.id]
    assert start.calls == [(matched.id, "external:github:evt-42")]


def test_same_external_event_id_is_sent_as_same_idempotency_key():
    matched = workflow("push")
    start = FakeStart()
    intake = ExternalEventIntake(FakeWorkflowRepository([matched]), start)

    event = ExternalEvent(
        source="github",
        event_type="push",
        payload={},
        event_id="evt-42",
    )

    intake.accept(event)
    intake.accept(event)

    assert start.calls == [
        (matched.id, "external:github:evt-42"),
        (matched.id, "external:github:evt-42"),
    ]


def test_different_external_event_ids_remain_independent():
    matched = workflow("push")
    start = FakeStart()
    intake = ExternalEventIntake(FakeWorkflowRepository([matched]), start)

    intake.accept(
        ExternalEvent(
            source="github",
            event_type="push",
            payload={},
            event_id="evt-1",
        )
    )
    intake.accept(
        ExternalEvent(
            source="github",
            event_type="push",
            payload={},
            event_id="evt-2",
        )
    )

    assert start.calls == [
        (matched.id, "external:github:evt-1"),
        (matched.id, "external:github:evt-2"),
    ]


def test_missing_external_event_id_does_not_become_idempotent():
    matched = workflow("push")
    start = FakeStart()
    intake = ExternalEventIntake(FakeWorkflowRepository([matched]), start)

    intake.accept(ExternalEvent(source="github", event_type="push", payload={}))
    intake.accept(ExternalEvent(source="github", event_type="push", payload={}))

    assert start.calls == [(matched.id, None), (matched.id, None)]
