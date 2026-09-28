from __future__ import annotations

from uuid import UUID

from app.domain.connection import Connection, ConnectionStatus
from app.domain.repositories import ConnectionRepository


class ConnectionNotFoundError(LookupError):
    pass


class ConnectionAccessDeniedError(PermissionError):
    pass


class ConnectionRevokedError(ValueError):
    pass


class ConnectionProviderMismatchError(ValueError):
    pass


class ConnectionResolver:
    """Resolve a tenant-owned connection without exposing secret material."""

    def __init__(self, repository: ConnectionRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        tenant_id: UUID,
        provider_id: str,
        reference: str,
    ) -> Connection:
        connection = self._repository.get_by_reference(
            reference.strip(),
            provider_id.strip(),
        )
        if connection is None:
            raise ConnectionNotFoundError(
                f"Connection not found: {provider_id}/{reference}"
            )

        if connection.tenant_id != tenant_id:
            raise ConnectionAccessDeniedError(
                "Connection belongs to a different tenant"
            )

        if connection.provider_id != provider_id.strip():
            raise ConnectionProviderMismatchError(
                "Connection provider does not match the requested provider"
            )

        if connection.status is ConnectionStatus.REVOKED:
            raise ConnectionRevokedError(
                f"Connection is revoked: {provider_id}/{reference}"
            )

        return connection
