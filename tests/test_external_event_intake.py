import pytest

from app.application.external_event_intake import ExternalEvent


def test_external_event_normalizes_deterministically():
    event = ExternalEvent(
        "stripe",
        "payment.completed",
        {"payment_id": "p1"},
        external_event_id="evt-1",
    )
    assert event.normalized_event().event_type == "payment.completed"


@pytest.mark.parametrize("source_id,event_type", [(" ", "created"), ("source", " ")])
def test_external_event_rejects_empty_source_or_type(source_id, event_type):
    with pytest.raises(ValueError):
        ExternalEvent(source_id, event_type, {}).normalized_event()


def test_external_event_rejects_blank_identity():
    with pytest.raises(ValueError, match="external_event_id"):
        ExternalEvent("source", "created", {}, external_event_id=" ").normalized_event()


def test_payload_is_preserved_without_affecting_normalized_event():
    event = ExternalEvent("source", "created", {"amount": 10})
    assert event.payload == {"amount": 10}
    assert event.normalized_event().event_type == "created"
