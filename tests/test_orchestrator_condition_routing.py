import pytest

from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.application.orchestrator import Orchestrator
from app.application.retry_policy import RetryPolicy
from app.domain.transition import Transition
from app.domain.workflow import Workflow, WorkflowStep


class SuccessfulDispatcher:
    def __init__(self):
        self.dispatched_capabilities = []

    def dispatch(self, capability_id, context):
        self.dispatched_capabilities.append(capability_id)
        return CapabilityResult.success(output={"value": "produced"})


class FakeConditionEvaluator:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def evaluate(self, condition: str, context: ExecutionContext) -> bool:
        self.calls.append((condition, context))
        return self.results[condition]


def create_branching_workflow():
    source = WorkflowStep.create("Source", "source")
    customer = WorkflowStep.create("Customer path", "customer")
    guest = WorkflowStep.create("Guest path", "guest")

    workflow = Workflow.create("Branching", [source, customer, guest])
    workflow.add_transition(Transition.create(source.id, customer.id, "is_customer"))
    workflow.add_transition(Transition.create(source.id, guest.id, "is_guest"))
    workflow.publish()

    return workflow, source, customer, guest


def test_orchestrator_selects_true_condition_transition():
    workflow, _, _, _ = create_branching_workflow()
    dispatcher = SuccessfulDispatcher()
    evaluator = FakeConditionEvaluator(
        {"is_customer": True, "is_guest": False}
    )

    execution = Orchestrator(
        dispatcher,
        RetryPolicy(),
        evaluator,
    ).start(workflow)

    assert dispatcher.dispatched_capabilities == ["source", "customer"]
    assert execution.current_step == 3
    assert execution.state.value == "completed"
    assert [condition for condition, _ in evaluator.calls] == [
        "is_customer",
        "is_guest",
    ]


def test_orchestrator_fails_routing_when_no_transition_is_eligible():
    workflow, _, _, _ = create_branching_workflow()
    evaluator = FakeConditionEvaluator(
        {"is_customer": False, "is_guest": False}
    )

    with pytest.raises(ValueError, match="No outgoing transition is eligible"):
        Orchestrator(
            SuccessfulDispatcher(),
            RetryPolicy(),
            evaluator,
        ).start(workflow)


def test_orchestrator_fails_routing_when_multiple_transitions_are_eligible():
    workflow, _, _, _ = create_branching_workflow()
    evaluator = FakeConditionEvaluator(
        {"is_customer": True, "is_guest": True}
    )

    with pytest.raises(ValueError, match="Multiple outgoing transitions are eligible"):
        Orchestrator(
            SuccessfulDispatcher(),
            RetryPolicy(),
            evaluator,
        ).start(workflow)


def test_orchestrator_requires_evaluator_for_conditional_transition():
    workflow, _, _, _ = create_branching_workflow()

    with pytest.raises(
        ValueError,
        match="Conditional transitions require a condition evaluator",
    ):
        Orchestrator(
            SuccessfulDispatcher(),
            RetryPolicy(),
        ).start(workflow)
