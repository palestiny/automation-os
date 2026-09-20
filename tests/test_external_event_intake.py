from __future__ import annotations

import pytest

from app.application.external_event_intake import ExternalEvent, ExternalEventIntake
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.trigger_invocation import TriggerInvocation
from app.domain.event import Event
from app.domain.workflow import Trigger, Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
    InMemoryExecutionStartRepository,
    InMemoryWorkflowRepository,
)


def test_external_event_normalizes_deterministically():
    external = ExternalEvent(
        source_id="stripe",
        event_type="payment.completed",
        payload={"payment_id": "p-1"},
        external_event_id="evt-1",
    )
    assert external.normalized_event() == Event.create("payment.completed")


@pytest.mark.parametrize("field", ["source_id", "event_type"])
def test_external_event_rejects_empty_required_identity(field):
    values = {"source_id": "source", "event_type": "event.created", "payload": {}}
    values[field] = " "
    with pytest.raises(ValueError):
        ExternalEvent(**values).normalized_event()


def test_external_event_rejects_blank_ids():
    with pytest.raises(ValueError, match="external_event_id"):
        ExternalEvent("source", "created", {}, external_event_id=" ").normalized_event()
    with pytest.raises(ValueError, match="idempotency_key"):
        ExternalEvent("source", "created", {}, idempotency_key=" ").normalized_event()


def test_payload_is_preserved_without_affecting_matching():
    external = ExternalEvent("source", "created", {"amount": 10})
    assert external.payload == {"amount": 10}
    assert external.normalized_event().event_type == "created"


class FakeTriggerInvocation:
    def __init__(self):
        self.calls = []

    def invoke(self, event, *, idempotency_key=None, idempotency_key_per_workflow=False):
        self.calls.append((event, idempotency_key, idempotency_key_per_workflow))
        return ("execution",)


def test_intake_delegates_only_through_trigger_invocation():
    invocation = FakeTriggerInvocation()
    result = ExternalEventIntake(invocation).intake(
        ExternalEvent("stripe", "payment.completed", {}, external_event_id="evt-1")
    )
    assert result == ("execution",)
    assert invocation.calls == [
        (Event.create("payment.completed"), "external-event:stripe:evt-1", True)
    ]


def _published_workflow(event_type: str) -> Workflow:
    workflow = Workflow.create(
        name=f"workflow-{event_type}",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        triggers=[Trigger(event_type=event_type)],
    )
    workflow.publish()
    return workflow


def _intake(repository):
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    starts = InMemoryExecutionStartRepository(executions, idempotency)
    starter = StartWorkflowExecution(
        repository,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=starts,
    )
    return ExternalEventIntake(TriggerInvocation(repository, starter)), executions


def test_same_external_event_id_is_deduplicated_per_matching_workflow():
    repository = InMemoryWorkflowRepository()
    first = _published_workflow("payment.completed")
    second = _published_workflow("payment.completed")
    repository.save(first)
    repository.save(second)
    intake, executions = _intake(repository)

    event = ExternalEvent(
        "stripe", "payment.completed", {}, external_event_id="evt-1"
    )
    first_result = intake.intake(event)
    second_result = intake.intake(event)

    assert {item.id for item in first_result} == {item.id for item in second_result}
    assert len(executions.all()) == 2


def test_different_external_event_ids_remain_independent():
    repository = InMemoryWorkflowRepository()
    repository.save(_published_workflow("payment.completed"))
    intake, executions = _intake(repository)

    intake.intake(ExternalEvent("stripe", "payment.completed", {}, external_event_id="evt-1"))
    intake.intake(ExternalEvent("stripe", "payment.completed", {}, external_event_id="evt-2"))

    assert len(executions.all()) == 2


def test_missing_external_event_id_is_non_idempotent():
    repository = InMemoryWorkflowRepository()
    repository.save(_published_workflow("payment.completed"))
    intake, executions = _intake(repository)

    event = ExternalEvent("stripe", "payment.completed", {})
    intake.intake(event)
    intake.intake(event)

    assert len(executions.all()) == 2


def test_caller_idempotency_key_is_used_without_external_event_id():
    invocation = FakeTriggerInvocation()
    ExternalEventIntake(invocation).intake(
        ExternalEvent("stripe", "payment.completed", {}, idempotency_key="caller-key")
    )
    assert invocation.calls[0][1] == "external-request:stripe:caller-key"
