from __future__ import annotations

from uuid import uuid4

from app.application.external_event_intake import ExternalEvent, ExternalEventIntake


class SpyTriggerInvocation:
    def __init__(self):
        self.calls = []

    def invoke(self, event, *, idempotency_key=None):
        self.calls.append((event, idempotency_key))
        return ()


def test_intake_delegates_normalized_event_and_external_idempotency():
    spy = SpyTriggerInvocation()
    intake = ExternalEventIntake(spy)

    intake.intake(
        ExternalEvent(
            source_id="stripe",
            event_type="payment.completed",
            payload={"id": "p1"},
            external_event_id="evt-123",
        )
    )

    event, key = spy.calls[0]
    assert event.event_type == "payment.completed"
    assert key == "external-event:stripe:evt-123"


def test_intake_uses_explicit_idempotency_key_when_external_id_is_absent():
    spy = SpyTriggerInvocation()
    intake = ExternalEventIntake(spy)

    intake.intake(
        ExternalEvent(
            source_id="source",
            event_type="event.created",
            payload={},
            idempotency_key="request-1",
        )
    )

    assert spy.calls[0][1] == "external-request:source:request-1"


def test_intake_without_identity_remains_non_idempotent():
    spy = SpyTriggerInvocation()
    intake = ExternalEventIntake(spy)

    intake.intake(
        ExternalEvent(
            source_id="source",
            event_type="event.created",
            payload={},
        )
    )

    assert spy.calls[0][1] is None
