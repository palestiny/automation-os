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


from app.application.external_event_intake import ExternalEventIntake
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.trigger_invocation import TriggerInvocation
from app.domain.workflow import Trigger, Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
    InMemoryExecutionStartRepository,
    InMemoryWorkflowRepository,
)


def _published_workflow(event_type: str) -> Workflow:
    item = Workflow.create(
        name=f"workflow-{event_type}",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        triggers=[Trigger(event_type=event_type)],
    )
    item.publish()
    return item


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


def test_intake_delegates_to_trigger_invocation_and_starts_matching_workflow():
    repository = InMemoryWorkflowRepository()
    workflow = _published_workflow("payment.completed")
    repository.save(workflow)
    intake, executions = _intake(repository)

    result = intake.intake(
        ExternalEvent(
            "stripe",
            "payment.completed",
            {"payment_id": "p1"},
            external_event_id="evt-1",
        )
    )

    assert len(result) == 1
    assert result[0].id == executions.all()[0].id


def test_same_external_event_is_deduplicated_per_matching_workflow():
    repository = InMemoryWorkflowRepository()
    first = _published_workflow("payment.completed")
    second = _published_workflow("payment.completed")
    repository.save(first)
    repository.save(second)
    intake, executions = _intake(repository)

    event = ExternalEvent(
        "stripe",
        "payment.completed",
        {"payment_id": "p1"},
        external_event_id="evt-1",
    )
    first_result = intake.intake(event)
    second_result = intake.intake(event)

    assert {item.id for item in first_result} == {item.id for item in second_result}
    assert len(executions.all()) == 2


def test_missing_external_event_id_is_non_idempotent():
    repository = InMemoryWorkflowRepository()
    workflow = _published_workflow("payment.completed")
    repository.save(workflow)
    intake, executions = _intake(repository)

    event = ExternalEvent("stripe", "payment.completed", {"payment_id": "p1"})
    intake.intake(event)
    intake.intake(event)

    assert len(executions.all()) == 2
