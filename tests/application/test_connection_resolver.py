from uuid import uuid4

import pytest

from app.application.connection_resolver import (
    ConnectionNotFoundError,
    ConnectionResolver,
    ConnectionRevokedError,
)
from app.domain.connection import Connection
from app.infrastructure.persistence.in_memory import InMemoryConnectionRepository


def make_connection(tenant_id):
    return Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )


def test_connection_repository_round_trips_tenant_owned_connection():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    connection = make_connection(tenant_id)

    repository.save(connection)

    assert repository.get(connection.id) == connection
    assert repository.get_by_reference("youtube.primary", "youtube") == connection


def test_connection_repository_hides_other_tenants():
    tenant_id = uuid4()
    other_tenant = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)

    repository.save(make_connection(tenant_id))

    other_repository = InMemoryConnectionRepository(tenant_id=other_tenant)

    assert other_repository.all() == ()


def test_connection_reference_is_unique_per_tenant_and_provider():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)

    repository.save(make_connection(tenant_id))

    with pytest.raises(ValueError, match="already exists"):
        repository.save(make_connection(tenant_id))


def test_resolver_returns_active_connection():
    tenant_id = uuid4()
    connection = make_connection(tenant_id)
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    repository.save(connection)

    result = ConnectionResolver(repository).resolve(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
    )

    assert result is connection


def test_resolver_fails_when_connection_is_missing():
    tenant_id = uuid4()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)

    with pytest.raises(ConnectionNotFoundError):
        ConnectionResolver(repository).resolve(
            tenant_id=tenant_id,
            provider_id="youtube",
            reference="youtube.primary",
        )


def test_resolver_fails_for_revoked_connection():
    tenant_id = uuid4()
    connection = make_connection(tenant_id)
    connection.revoke()
    repository = InMemoryConnectionRepository(tenant_id=tenant_id)
    repository.save(connection)

    with pytest.raises(ConnectionRevokedError):
        ConnectionResolver(repository).resolve(
            tenant_id=tenant_id,
            provider_id="youtube",
            reference="youtube.primary",
        )


def test_resolver_does_not_cross_tenant_boundary():
    owner_tenant = uuid4()
    other_tenant = uuid4()
    owner_repository = InMemoryConnectionRepository(tenant_id=owner_tenant)
    owner_repository.save(make_connection(owner_tenant))

    other_repository = InMemoryConnectionRepository(tenant_id=other_tenant)

    with pytest.raises(ConnectionNotFoundError):
        ConnectionResolver(other_repository).resolve(
            tenant_id=other_tenant,
            provider_id="youtube",
            reference="youtube.primary",
        )
