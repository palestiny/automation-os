import pytest

from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.domain.workflow import Condition


def evaluate(operator: str, left: object, right: object) -> bool:
    context = ExecutionContext()
    context.set("value", left)
    return ConditionEvaluator().evaluate(
        Condition.create("value", operator, right),
        context,
    )


@pytest.mark.parametrize(
    ("operator", "left", "right", "expected"),
    [
        ("equals", 10, 10, True),
        ("equals", 10, 20, False),
        ("not_equals", 10, 20, True),
        ("not_equals", 10, 10, False),
        ("greater_than", 20, 10, True),
        ("greater_than", 10, 20, False),
        ("greater_than_or_equal", 10, 10, True),
        ("greater_than_or_equal", 9, 10, False),
        ("less_than", 9, 10, True),
        ("less_than", 10, 9, False),
        ("less_than_or_equal", 10, 10, True),
        ("less_than_or_equal", 11, 10, False),
    ],
)
def test_condition_evaluator(operator, left, right, expected):
    assert evaluate(operator, left, right) is expected


def test_condition_evaluator_reads_execution_context():
    context = ExecutionContext()
    context.set("video.duration", 120)

    condition = Condition.create("video.duration", "greater_than", 60)

    assert ConditionEvaluator().evaluate(condition, context) is True


def test_condition_evaluator_rejects_missing_context_value():
    condition = Condition.create("video.duration", "greater_than", 60)

    with pytest.raises(ValueError, match="not found"):
        ConditionEvaluator().evaluate(condition, ExecutionContext())


def test_condition_evaluator_rejects_unsupported_operator():
    context = ExecutionContext()
    context.set("value", 10)
    condition = Condition.create("value", "contains", 10)

    with pytest.raises(ValueError, match="Unsupported condition operator"):
        ConditionEvaluator().evaluate(condition, context)
