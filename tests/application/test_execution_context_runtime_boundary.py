import pytest

from app.application.execution_context import ExecutionContext


def test_caller_cannot_set_protected_runtime_context():
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.set("runtime.connections", object())


def test_runtime_context_requires_reserved_prefix():
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.set_runtime("connections", object())


def test_runtime_context_is_readable_after_application_preparation():
    context = ExecutionContext()
    value = object()
    context.set_runtime("runtime.connections", value)
    assert context.get_runtime("runtime.connections") is value
