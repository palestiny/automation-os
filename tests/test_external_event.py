from dataclasses import FrozenInstanceError

import pytest

from app.domain.event import Event


def test_external_event_preserves_source_id_and_payload():
    payload = {"customer_id": "42", "amount": 100}

    event = Event.create(
        "payment.completed",
        source="stripe",
        external_event_id="evt_123",
        payload=payload,
    )

    assert event.event_type == "payment.completed"
    assert event.source == "stripe"
    assert event.external_event_id == "evt_123"
    assert event.payload == payload


def test_event_payload_is_copied_at_creation():
    payload = {"customer_id": "42"}
    event = Event.create("payment.completed", payload=payload)

    payload["customer_id"] = "changed"

    assert event.payload == {"customer_id": "42"}


def test_event_rejects_empty_source():
    with pytest.raises(ValueError, match="source"):
        Event.create("payment.completed", source=" ")


def test_event_rejects_empty_external_id():
    with pytest.raises(ValueError, match="external_event_id"):
        Event.create("payment.completed", external_event_id=" ")


def test_event_remains_immutable():
    event = Event.create("payment.completed")

    with pytest.raises(FrozenInstanceError):
        event.event_type = "payment.failed"
