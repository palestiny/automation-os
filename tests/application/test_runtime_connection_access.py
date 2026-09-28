from uuid import uuid4

import pytest

from app.application.connection_runtime_access import (
    RUNTIME_CONNECTIONS_KEY,
    get_prepared_connection,
)
from app.application.connection_runtime_resolution import ResolvedConnection
from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PreparedRuntimeConnections


def test_runtime_access_requires_preparation():
    with pytest.raises(RuntimeError):
        get_prepared_connection(ExecutionContext(), provider_id="youtube", reference="youtube.primary")


def test_runtime_access_returns_only_declared_connection():
    tenant_id = uuid4()
    connection = ResolvedConnection(
        connection_id=uuid4(), tenant_id=tenant_id, provider_id="youtube",
        reference="youtube.primary", authentication_type="api_key",
        secret_material=object(),
    )
    context = ExecutionContext()
    context.set(RUNTIME_CONNECTIONS_KEY, PreparedRuntimeConnections((connection,)))

    assert get_prepared_connection(
        context, provider_id="youtube", reference="youtube.primary"
    ) is connection

    with pytest.raises(RuntimeError):
        get_prepared_connection(context, provider_id="youtube", reference="youtube.other")
