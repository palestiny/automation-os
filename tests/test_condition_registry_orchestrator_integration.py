import pytest

from app.application.capability_result import CapabilityResult
from app.application.condition_registry import ConditionRegistry
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


def create_branching_workflow(first_condition: str, second_condition: str):
    source = WorkflowStep.create("Source", "source")
    customer = WorkflowStep.create("Customer path", "customer")
    guest = WorkflowStep.create("Guest path", "guest")

    workflow = Workflow.create("Branching", [source, customer, guest])
    workflow.add_transition(
        Transition.create(source.id, customer.id, first_condition)
    )
    workflow.add_transition(
        Transition.create(source.id, guest.id, second_condition)
    )
    workflow.publish()

    return workflow


def test_registered_conditions_drive_orchestrator_routing():
    workflow = create_branching_workflow("is_customer", "is_guest")

    registry = ConditionRegistry()
    registry.register(
        "is_customer",
        lambda context: context.get("customer") is not None,
    )
    registry.register(
        "is_guest",
        lambda context: context.get("customer") is None,
    )

    dispatcher = SuccessfulDispatcher()
    execution = Orchestrator(
        dispatcher,
        RetryPolicy(),
        registry,
    ).start(workflow)

    assert dispatcher.dispatched_capabilities == ["source", "customer"]
    assert execution.current_step == 3
    assert execution.state.value == "completed"


def test_condition_registry_receives_execution_context_from_orchestrator():
    workflow = create_branching_workflow("has_customer", "no_customer")

    registry = ConditionRegistry()
    received_contexts = []

    def has_customer(context: ExecutionContext) -> bool:
        received_contexts.append(context)
        return False

    def no_customer(context: ExecutionContext) -> bool:
        received_contexts.append(context)
        return True

    registry.register("has_customer", has_customer)
    registry.register("no_customer", no_customer)

    Orchestrator(SuccessfulDispatcher(), RetryPolicy(), registry).start(workflow)

    assert len(received_contexts) == 2
    assert received_contexts[0] is received_contexts[1]


def test_orchestrator_surfaces_unregistered_condition():
    workflow = create_branching_workflow("is_customer", "is_guest")

    registry = ConditionRegistry()
    registry.register("is_customer", lambda context: True)

    with pytest.raises(ValueError, match="Condition is not registered"):
        Orchestrator(SuccessfulDispatcher(), RetryPolicy(), registry).start(workflow)
