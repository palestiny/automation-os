import pytest

from app.application.execution_context import ExecutionContext


def test_caller_cannot_write_protected_runtime_namespace():
    context = ExecutionContext()
    with pytest.raises(PermissionError):
        context.set("runtime.connections", object())


def test_runtime_owner_can_write_protected_namespace():
    context = ExecutionContext()
    value = object()
    context._set_runtime("runtime.connections", value)
    assert context.get_runtime("runtime.connections") is value


def test_runtime_namespace_rejects_unscoped_keys():
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context._set_runtime("connections", object())


def test_get_runtime_requires_protected_namespace():
    context = ExecutionContext()
    with pytest.raises(ValueError):
        context.get_runtime("connections")
