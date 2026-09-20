from app.application.external_event_intake import ExternalEvent
from app.application.external_event_intake_service import ExternalEventIntake


class SpyTriggerInvocation:
    def __init__(self):
        self.calls = []

    def invoke(self, event, *, idempotency_key=None):
        self.calls.append((event, idempotency_key))
        return ()


def test_intake_delegates_normalized_event_and_external_idempotency():
    spy = SpyTriggerInvocation()
    ExternalEventIntake(spy).intake(
        ExternalEvent("stripe", "payment.completed", {"id": "p1"}, external_event_id="evt-123")
    )
    event, key = spy.calls[0]
    assert event.event_type == "payment.completed"
    assert key == "external:stripe:evt-123"


def test_intake_uses_explicit_key_when_external_id_is_absent():
    spy = SpyTriggerInvocation()
    ExternalEventIntake(spy).intake(
        ExternalEvent("source", "event.created", {}, idempotency_key="request-1")
    )
    assert spy.calls[0][1] == "external-key:source:request-1"


def test_intake_without_identity_is_non_idempotent():
    spy = SpyTriggerInvocation()
    ExternalEventIntake(spy).intake(ExternalEvent("source", "event.created", {}))
    assert spy.calls[0][1] is None
