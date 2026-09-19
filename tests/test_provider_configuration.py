import pytest

from app.infrastructure.provider import ProviderConfiguration


def test_provider_configuration_is_immutable_and_provider_neutral():
    config = ProviderConfiguration(
        provider_id="openai",
        service_id="gpt-test",
        credentials_ref="OPENAI_API_KEY",
    )

    assert config.provider == "openai"
    assert config.service == "gpt-test"
    assert config.credentials_ref == "OPENAI_API_KEY"

    with pytest.raises(AttributeError):
        config.provider_id = "other"


def test_provider_configuration_rejects_empty_identity():
    with pytest.raises(ValueError, match="provider_id"):
        ProviderConfiguration("", "service")

    with pytest.raises(ValueError, match="service_id"):
        ProviderConfiguration("provider", "")


def test_provider_configuration_rejects_empty_optional_values():
    with pytest.raises(ValueError, match="endpoint"):
        ProviderConfiguration("provider", "service", endpoint=" ")

    with pytest.raises(ValueError, match="credentials_ref"):
        ProviderConfiguration("provider", "service", credentials_ref=" ")
