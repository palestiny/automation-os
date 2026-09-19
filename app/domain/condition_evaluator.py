from __future__ import annotations

from enum import Enum
from typing import Any

from app.domain.workflow import Condition


class ConditionResult(Enum):
    TRUE = "true"
    FALSE = "false"
    INVALID = "invalid"


class ConditionEvaluator:
    """Pure deterministic evaluator for workflow conditions."""

    _OPERATORS = {
        "equals",
        "not_equals",
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "contains",
        "not_contains",
        "exists",
        "not_exists",
    }

    def evaluate(self, condition: Condition, context: dict[str, Any]) -> ConditionResult:
        if not isinstance(condition, Condition):
            raise ValueError("Condition must be a Condition instance")
        if not isinstance(context, dict):
            raise ValueError("Condition context must be a dictionary")

        operator = condition.operator.strip()
        if operator not in self._OPERATORS:
            return ConditionResult.INVALID

        exists, left = self._resolve(context, condition.left_operand)
        if operator == "exists":
            return ConditionResult.TRUE if exists else ConditionResult.FALSE
        if operator == "not_exists":
            return ConditionResult.FALSE if exists else ConditionResult.TRUE
        if not exists:
            return ConditionResult.INVALID

        right = condition.right_operand
        try:
            if operator == "equals":
                matched = left == right
            elif operator == "not_equals":
                matched = left != right
            elif operator == "greater_than":
                matched = left > right
            elif operator == "greater_than_or_equal":
                matched = left >= right
            elif operator == "less_than":
                matched = left < right
            elif operator == "less_than_or_equal":
                matched = left <= right
            elif operator == "contains":
                matched = right in left
            else:
                matched = right not in left
        except (TypeError, ValueError):
            return ConditionResult.INVALID

        return ConditionResult.TRUE if matched else ConditionResult.FALSE

    @staticmethod
    def _resolve(context: dict[str, Any], path: str) -> tuple[bool, Any]:
        current: Any = context
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current
