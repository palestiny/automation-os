from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.connection import Connection, ConnectionStatus


def test_connection_requires_tenant_provider_and_reference():
    tenant_id = uuid4()

    connection = Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )

    assert connection.tenant_id == tenant_id
    assert connection.provider_id == "youtube"
    assert connection.reference == "youtube.primary"
    assert connection.authentication_type == "api_key"
    assert connection.secret_reference == "secret://youtube/primary"
    assert connection.status is ConnectionStatus.ACTIVE


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider_id": "", "reference": "primary"},
        {"provider_id": "youtube", "reference": ""},
        {"provider_id": "youtube", "reference": "youtube.primary", "secret_reference": ""},
    ],
)
def test_connection_rejects_empty_identity_or_secret_reference(kwargs):
    base = {
        "tenant_id": uuid4(),
        "provider_id": "youtube",
        "reference": "youtube.primary",
        "authentication_type": "api_key",
        "secret_reference": "secret://youtube/primary",
    }
    base.update(kwargs)

    with pytest.raises(ValueError):
        Connection.create(**base)


def test_connection_requires_uuid_tenant():
    with pytest.raises(ValueError):
        Connection.create(
            tenant_id="tenant",
            provider_id="youtube",
            reference="youtube.primary",
            authentication_type="api_key",
            secret_reference="secret://youtube/primary",
        )


def test_connection_can_be_revoked_but_not_reactivated_by_runtime():
    connection = Connection.create(
        tenant_id=uuid4(),
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
    )

    connection.revoke()

    assert connection.status is ConnectionStatus.REVOKED

    with pytest.raises(ValueError, match="revoked"):
        connection.revoke()
