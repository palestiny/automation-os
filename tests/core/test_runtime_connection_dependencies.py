from uuid import uuid4

import pytest

from app.application.secret_provider import SecretProvider
from app.core.runtime_connection_dependencies import build_runtime_connection_preparer


class FakeSecretProvider:
    def get_secret(self, secret_reference: str) -> object:
        return {"secret_reference": secret_reference}


def test_runtime_connection_composition_requires_explicit_tenant():
    tenant_id = uuid4()
    preparer = build_runtime_connection_preparer(
        tenant_id=tenant_id,
        secret_provider=FakeSecretProvider(),
    )
    assert preparer is not None


def test_runtime_connection_composition_rejects_non_uuid_tenant():
    with pytest.raises(TypeError):
        build_runtime_connection_preparer(
            tenant_id="tenant-1",
            secret_provider=FakeSecretProvider(),
        )


def test_fake_secret_provider_satisfies_runtime_protocol():
    provider = FakeSecretProvider()
    assert isinstance(provider, SecretProvider)
