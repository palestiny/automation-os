from __future__ import annotations

import pytest

from app.application.external_event_intake import ExternalEvent


def test_external_event_normalizes_deterministically():
    external = ExternalEvent(
        source_id="stripe",
        event_type="payment.completed",
        payload={"payment_id": "p-1"},
        external_event_id="evt-1",
    )

    assert external.normalized_event().event_type == "payment.completed"


@pytest.mark.parametrize(
    "field",
    ["source_id", "event_type"],
)
def test_external_event_rejects_empty_required_identity(field):
    values = {
        "source_id": "source",
        "event_type": "event.created",
        "payload": {},
    }
    values[field] = " "

    with pytest.raises(ValueError):
        ExternalEvent(**values).normalized_event()


def test_external_event_preserves_payload_without_using_it_for_matching():
    external = ExternalEvent(
        source_id="source",
        event_type="event.created",
        payload={"important": "data"},
    )

    assert external.payload == {"important": "data"}
    assert external.normalized_event().event_type == "event.created"


def test_external_event_rejects_blank_external_event_id():
    external = ExternalEvent(
        source_id="source",
        event_type="event.created",
        payload={},
        external_event_id=" ",
    )

    with pytest.raises(ValueError, match="external_event_id"):
        external.normalized_event()
