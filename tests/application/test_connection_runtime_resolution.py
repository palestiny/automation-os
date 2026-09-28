from uuid import uuid4

import pytest

from app.application.connection_resolver import ConnectionResolver, ConnectionNotFoundError
from app.application.connection_runtime_resolution import ResolveRuntimeConnection
from app.application.secret_provider import SecretProvider
from app.domain.connection import Connection
from app.infrastructure.persistence.in_memory import InMemoryConnectionRepository


class FakeSecretProvider:
    def __init__(self, values):
        self.values = values
        self.references = []

    def get_secret(self, secret_reference):
        self.references.append(secret_reference)
        try:
            return self.values[secret_reference]
        except KeyError as exc:
            raise RuntimeError("secret missing") from exc


def test_runtime_resolution_returns_connection_metadata_and_protected_secret():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    connection = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )
    repository.save(connection)

    resolver = ResolveRuntimeConnection(
        ConnectionResolver(repository),
        FakeSecretProvider({"secret://youtube/primary": "TOP-SECRET"}),
    )

    resolved = resolver.resolve(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
    )

    assert resolved.connection_id == connection.id
    assert resolved.tenant_id == tenant_id
    assert resolved.provider_id == "youtube"
    assert resolved.reference == "youtube.primary"
    assert resolved.authentication_type == "api_key"
    assert resolved.secret_material == "TOP-SECRET"
    assert "TOP-SECRET" not in repr(resolved)


def test_runtime_resolution_uses_connection_secret_reference_not_raw_reference():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    connection = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )
    repository.save(connection)
    provider = FakeSecretProvider({"secret://youtube/primary": "TOP-SECRET"})

    ResolveRuntimeConnection(
        ConnectionResolver(repository),
        provider,
    ).resolve(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
    )

    assert provider.references == ["secret://youtube/primary"]


def test_runtime_resolution_fails_when_protected_secret_cannot_be_resolved():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    connection = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )
    repository.save(connection)

    resolver = ResolveRuntimeConnection(
        ConnectionResolver(repository),
        FakeSecretProvider({}),
    )

    with pytest.raises(RuntimeError, match="Protected secret resolution failed"):
        resolver.resolve(
            tenant_id=tenant_id,
            provider_id="youtube",
            reference="youtube.primary",
        )


def test_runtime_resolution_preserves_connection_not_found_boundary():
    tenant_id = uuid4()
    resolver = ResolveRuntimeConnection(
        ConnectionResolver(InMemoryConnectionRepository(tenant_id=tenant_id)),
        FakeSecretProvider({}),
    )

    with pytest.raises(ConnectionNotFoundError):
        resolver.resolve(
            tenant_id=tenant_id,
            provider_id="youtube",
            reference="youtube.primary",
        )


def test_secret_provider_satisfies_application_contract():
    assert isinstance(FakeSecretProvider({}), SecretProvider)
