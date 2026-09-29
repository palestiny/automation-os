from uuid import uuid4

from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PreparedRuntimeConnections


def test_caller_cannot_write_protected_runtime_connection_slot():
    context = ExecutionContext()
    context.set("runtime.connections", "attacker-controlled")
    assert context.get_runtime_connections() == ()


def test_runtime_connections_are_available_only_after_preparation():
    context = ExecutionContext()
    connection = object()
    context._set_runtime_connections((connection,))
    assert context.get_runtime_connections() == (connection,)


def test_prepared_runtime_connections_repr_does_not_expose_material():
    prepared = PreparedRuntimeConnections(())
    assert "secret" not in repr(prepared).lower()
