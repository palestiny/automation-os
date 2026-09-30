from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from app.application.connection_resolver import ConnectionResolver
from app.application.connection_runtime_resolution import ResolveRuntimeConnection
from app.application.runtime_connection_preparation import (
    PrepareWorkflowRuntimeConnections,
)
from app.application.secret_provider import SecretProvider
from app.domain.repositories import ConnectionRepository


class RuntimeConnectionPreparerFactory:
    """Create execution-scoped runtime preparation services.

    The factory owns no tenant state. Each execution supplies the persisted
    tenant id, and the injected repository factory binds all connection
    persistence to that tenant before resolution begins.
    """

    def __init__(
        self,
        connection_repository_factory: Callable[[UUID], ConnectionRepository],
        secret_provider: SecretProvider,
    ) -> None:
        self._connection_repository_factory = connection_repository_factory
        self._secret_provider = secret_provider

    def create(self, tenant_id: UUID) -> PrepareWorkflowRuntimeConnections:
        repository = self._connection_repository_factory(tenant_id)
        resolver = ConnectionResolver(repository)
        runtime_resolver = ResolveRuntimeConnection(
            resolver,
            self._secret_provider,
        )
        return PrepareWorkflowRuntimeConnections(runtime_resolver)
