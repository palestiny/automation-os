from uuid import UUID

from app.application.external_event_intake import ExternalEvent, ExternalEventIntake
from app.application.trigger_invocation import TriggerInvocation
from app.domain.workflow import Trigger, Workflow, WorkflowState, WorkflowStep


class FakeWorkflowRepository:
    def __init__(self, workflows):
        self._workflows = workflows

    def all(self):
        return tuple(self._workflows)


class FakeStarter:
    def __init__(self):
        self.calls = []
        self.results = {}

    def execute(self, workflow_id, *, idempotency_key=None):
        self.calls.append((workflow_id, idempotency_key))
        result = object()
        self.results[workflow_id] = result
        return result


def workflow(workflow_id, event_type="video.uploaded"):
    return Workflow(
        id=UUID(workflow_id),
        name="External event workflow",
        _steps=[WorkflowStep.create("Process", "test")],
        state=WorkflowState.PUBLISHED,
        _triggers=[Trigger.create(event_type)],
    )


def test_external_event_normalizes_payload_and_delegates_to_trigger_invocation():
    starter = FakeStarter()
    workflow_instance = workflow("00000000-0000-0000-0000-000000000001")
    intake = ExternalEventIntake(
        TriggerInvocation(FakeWorkflowRepository([workflow_instance]), starter)
    )

    result = intake.ingest(
        ExternalEvent(
            source_id="github",
            event_type="video.uploaded",
            event_id="evt-1",
            payload={"repository": "automation-os"},
        )
    )

    assert result.executions == (starter.results[workflow_instance.id],)
    assert starter.calls == [
        (
            workflow_instance.id,
            f"external:github:evt-1:{workflow_instance.id}",
        )
    ]


def test_external_event_without_id_is_not_made_idempotent():
    starter = FakeStarter()
    workflow_instance = workflow("00000000-0000-0000-0000-000000000001")
    intake = ExternalEventIntake(
        TriggerInvocation(FakeWorkflowRepository([workflow_instance]), starter)
    )

    intake.ingest(
        ExternalEvent(source_id="poller", event_type="video.uploaded")
    )

    assert starter.calls == [(workflow_instance.id, None)]


def test_external_event_validation_rejects_empty_source():
    try:
        ExternalEvent(source_id=" ", event_type="video.uploaded")
    except ValueError as exc:
        assert str(exc) == "External event source_id cannot be empty"
    else:
        raise AssertionError("expected ValueError")


def test_external_event_validation_rejects_empty_event_id_when_supplied():
    try:
        ExternalEvent(
            source_id="github",
            event_type="video.uploaded",
            event_id=" ",
        )
    except ValueError as exc:
        assert "event_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")
