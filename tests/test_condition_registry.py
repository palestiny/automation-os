import pytest

from app.application.condition_registry import ConditionRegistry
from app.application.execution_context import ExecutionContext


def test_registry_evaluates_registered_condition():
    registry = ConditionRegistry()
    context = ExecutionContext()
    registry.register("is_customer", lambda ctx: ctx.get("customer") is not None)
    context.set("customer", {"id": 1})

    assert registry.evaluate("is_customer", context) is True


def test_registry_rejects_duplicate_condition_name():
    registry = ConditionRegistry()
    registry.register("is_customer", lambda ctx: True)

    with pytest.raises(ValueError, match="Condition is already registered"):
        registry.register("is_customer", lambda ctx: False)


def test_registry_rejects_unknown_condition():
    registry = ConditionRegistry()
    context = ExecutionContext()

    with pytest.raises(ValueError, match="Condition is not registered"):
        registry.evaluate("is_customer", context)


def test_registry_rejects_blank_condition_name():
    registry = ConditionRegistry()

    with pytest.raises(ValueError, match="Condition name cannot be blank"):
        registry.register("   ", lambda ctx: True)
