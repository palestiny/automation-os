from __future__ import annotations

from app.application.execution_context import ExecutionContext
from app.domain.workflow import Condition


class ConditionEvaluator:
    """Evaluate a declarative Condition against execution-scoped context."""

    def evaluate(
        self,
        condition: Condition,
        context: ExecutionContext,
    ) -> bool:
        try:
            left = context.get(condition.left_operand)
        except KeyError as exc:
            raise ValueError(
                f"Condition operand not found in execution context: "
                f"{condition.left_operand}"
            ) from exc

        if condition.operator == "equals":
            return left == condition.right_operand
        if condition.operator == "not_equals":
            return left != condition.right_operand
        if condition.operator == "greater_than":
            return left > condition.right_operand
        if condition.operator == "greater_than_or_equal":
            return left >= condition.right_operand
        if condition.operator == "less_than":
            return left < condition.right_operand
        if condition.operator == "less_than_or_equal":
            return left <= condition.right_operand

        raise ValueError(
            f"Unsupported condition operator: {condition.operator}"
        )
