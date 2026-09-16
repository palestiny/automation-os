from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext


class FakeConditionEvaluator:
    def __init__(self, results: dict[str, bool]):
        self.results = results
        self.calls = []

    def evaluate(self, condition: str, context: ExecutionContext) -> bool:
        self.calls.append((condition, context))
        return self.results[condition]


def test_condition_evaluator_receives_condition_reference_and_context() -> None:
    evaluator: ConditionEvaluator = FakeConditionEvaluator(
        {"is_customer": True}
    )
    context = ExecutionContext()

    assert evaluator.evaluate("is_customer", context) is True
