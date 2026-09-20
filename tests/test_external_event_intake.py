from __future__ import annotations

import pytest

from app.application.external_event_intake import ExternalEvent, ExternalEventIntake
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.trigger_invocation import TriggerInvocation
from app.domain.event import Event
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository, InMemoryWorkflowRepository


def _workflow(event_type: str) -> Workflow:
    workflow = Workflow.create(
        name="external workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        triggers=[event_type],
    )
    workflow.publish()
    return workflow


def _intake():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    starter = StartWorkflowExecution(workflows, executions)
    invocation = TriggerInvocation(workflows, starter)
    return workflows, executions, ExternalEventIntake(invocation)


def test_valid_external_event_is_normalized_and_invokes_published_workflow():
    workflows, executions, intake = _intake()
    workflow = _workflow("payment.received")
    workflows.save(workflow)

    result = intake.receive(ExternalEvent("stripe", "payment.received", "evt-1", {"amount": 100}))

    assert len(result.executions) == 1
    assert result.event == Event.create("payment.received", source="stripe", external_event_id="evt-1", payload={"amount": 100})
    assert executions.get(result.executions[0].id) is not None


def test_invalid_external_source_or_type_is_rejected():
    _, _, intake = _intake()
    with pytest.raises(ValueError, match="source"):
        intake.receive(ExternalEvent(" ", "payment.received"))
    with pytest.raises(ValueError, match="event type"):
        intake.receive(ExternalEvent("stripe", " "))


def test_draft_workflow_does_not_execute():
    workflows, executions, intake = _intake()
    workflow = Workflow.create(
        name="draft",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        triggers=["payment.received"],
    )
    workflows.save(workflow)
    result = intake.receive(ExternalEvent("stripe", "payment.received", "evt-2"))
    assert result.executions == ()
    assert executions.all() == ()


def test_same_external_event_id_is_deduplicated():
    workflows, executions, intake = _intake()
    workflow = _workflow("payment.received")
    workflows.save(workflow)
    event = ExternalEvent("stripe", "payment.received", "evt-3")
    first = intake.receive(event)
    second = intake.receive(event)
    assert [item.id for item in second.executions] == [first.executions[0].id]
    assert len(executions.all()) == 1


def test_different_external_event_ids_remain_independent():
    workflows, executions, intake = _intake()
    workflow = _workflow("payment.received")
    workflows.save(workflow)
    first = intake.receive(ExternalEvent("stripe", "payment.received", "evt-4"))
    second = intake.receive(ExternalEvent("stripe", "payment.received", "evt-5"))
    assert first.executions[0].id != second.executions[0].id
    assert len(executions.all()) == 2


def test_missing_external_event_id_is_not_accidentally_idempotent():
    workflows, executions, intake = _intake()
    workflow = _workflow("payment.received")
    workflows.save(workflow)
    first = intake.receive(ExternalEvent("stripe", "payment.received"))
    second = intake.receive(ExternalEvent("stripe", "payment.received"))
    assert first.executions[0].id != second.executions[0].id
    assert len(executions.all()) == 2


def test_payload_is_preserved_while_matching_remains_event_type_only():
    _, _, intake = _intake()
    result = intake.receive(ExternalEvent("stripe", "payment.received", "evt-6", {"amount": 250}))
    assert result.event.payload == {"amount": 250}
