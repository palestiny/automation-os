from uuid import uuid4

import pytest

from app.application.human_decision import (
    HumanDecision,
    HumanDecisionPort,
    HumanDecisionRequest,
)
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def waiting_execution():
    execution = Execution.create(uuid4())
    execution.start()
    execution.wait()
    return execution


def test_human_decision_request_is_explicit_and_pending():
    execution = waiting_execution()
    port = HumanDecisionPort(InMemoryExecutionRepository())

    request = port.request(
        execution_id=execution.id,
        prompt="Approve publishing this result?",
        context={"risk": "low"},
    )

    assert isinstance(request, HumanDecisionRequest)
    assert request.execution_id == execution.id
    assert request.prompt == "Approve publishing this result?"
    assert request.context == {"risk": "low"}
    assert request.decision is None


def test_approve_resumes_waiting_execution():
    execution = waiting_execution()
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    request = port.request(execution.id, "Approve?", {})
    result = port.decide(request.id, HumanDecision.APPROVED)

    assert result.decision is HumanDecision.APPROVED
    assert repository.get(execution.id).state is ExecutionState.RUNNING


def test_reject_resumes_waiting_execution_with_rejected_decision():
    execution = waiting_execution()
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    request = port.request(execution.id, "Approve?", {})
    result = port.decide(request.id, HumanDecision.REJECTED)

    assert result.decision is HumanDecision.REJECTED
    assert repository.get(execution.id).state is ExecutionState.RUNNING


def test_decision_requires_waiting_execution():
    execution = Execution.create(uuid4())
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    with pytest.raises(ValueError, match="WAITING"):
        port.request(execution.id, "Approve?", {})


def test_same_decision_is_idempotent():
    execution = waiting_execution()
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    request = port.request(execution.id, "Approve?", {})
    first = port.decide(request.id, HumanDecision.APPROVED)
    second = port.decide(request.id, HumanDecision.APPROVED)

    assert second == first
    assert repository.get(execution.id).state is ExecutionState.RUNNING


def test_conflicting_decision_is_rejected():
    execution = waiting_execution()
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    request = port.request(execution.id, "Approve?", {})
    port.decide(request.id, HumanDecision.APPROVED)

    with pytest.raises(ValueError, match="already decided"):
        port.decide(request.id, HumanDecision.REJECTED)


def test_decision_request_is_not_created_for_missing_execution():
    repository = InMemoryExecutionRepository()
    port = HumanDecisionPort(repository)

    with pytest.raises(ValueError, match="Execution not found"):
        port.request(uuid4(), "Approve?", {})


def test_decision_request_is_scoped_to_execution_state_not_provider_execution():
    execution = waiting_execution()
    repository = InMemoryExecutionRepository()
    repository.save(execution)
    port = HumanDecisionPort(repository)

    request = port.request(execution.id, "Approve?", {"source": "human"})

    assert request.id != execution.id
    assert request.context["source"] == "human"
