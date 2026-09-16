import pytest

from app.domain.transition import Transition
from app.domain.workflow import Workflow, WorkflowStep


def test_linear_workflow_graph_is_reachable() -> None:
    step1 = WorkflowStep.create("First", "first")
    step2 = WorkflowStep.create("Second", "second")
    step3 = WorkflowStep.create("Third", "third")
    workflow = Workflow.create("Linear", [step1, step2, step3])

    workflow.add_transition(Transition.create(step1.id, step2.id))
    workflow.add_transition(Transition.create(step2.id, step3.id))

    workflow.validate_graph()


def test_branching_workflow_graph_is_reachable() -> None:
    source = WorkflowStep.create("Source", "source")
    customer = WorkflowStep.create("Customer", "customer")
    guest = WorkflowStep.create("Guest", "guest")
    workflow = Workflow.create("Branching", [source, customer, guest])

    workflow.add_transition(Transition.create(source.id, customer.id, "is_customer"))
    workflow.add_transition(Transition.create(source.id, guest.id, "is_guest"))

    workflow.validate_graph()


def test_unreachable_workflow_step_is_rejected() -> None:
    first = WorkflowStep.create("First", "first")
    second = WorkflowStep.create("Second", "second")
    unreachable = WorkflowStep.create("Unreachable", "unreachable")
    workflow = Workflow.create("Invalid", [first, second, unreachable])

    workflow.add_transition(Transition.create(first.id, second.id))

    with pytest.raises(ValueError, match="unreachable steps"):
        workflow.validate_graph()


def test_conditional_transition_counts_as_structural_edge_without_evaluation() -> None:
    source = WorkflowStep.create("Source", "source")
    target = WorkflowStep.create("Target", "target")
    workflow = Workflow.create("Conditional", [source, target])

    workflow.add_transition(Transition.create(source.id, target.id, "runtime_condition"))

    workflow.validate_graph()


def test_graph_validation_does_not_mutate_workflow() -> None:
    first = WorkflowStep.create("First", "first")
    second = WorkflowStep.create("Second", "second")
    workflow = Workflow.create("Stable", [first, second])
    transition = Transition.create(first.id, second.id)
    workflow.add_transition(transition)

    steps_before = workflow.steps
    transitions_before = workflow.transitions

    workflow.validate_graph()

    assert workflow.steps == steps_before
    assert workflow.transitions == transitions_before
