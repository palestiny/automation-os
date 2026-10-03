import pytest

from app.application.secret_provider import SecretResolutionError
from app.infrastructure.aws_secrets_manager import AwsSecretsManagerProvider


class FakeSecretsManagerClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.secret_ids = []

    def get_secret_value(self, *, SecretId):
        self.secret_ids.append(SecretId)
        if self.error:
            raise self.error
        return self.response


def test_aws_secret_provider_resolves_secret_string_without_exposing_provider_details():
    client = FakeSecretsManagerClient(response={"SecretString": "super-secret"})
    provider = AwsSecretsManagerProvider(
        secret_prefix="automation-os/prod/tenant-1",
        client=client,
    )

    assert provider.get_secret("connections/google") == "super-secret"
    assert client.secret_ids == ["automation-os/prod/tenant-1/connections/google"]


def test_aws_secret_provider_resolves_secret_binary():
    client = FakeSecretsManagerClient(response={"SecretBinary": b"secret-bytes"})
    provider = AwsSecretsManagerProvider(
        secret_prefix="automation-os/prod/tenant-1",
        client=client,
    )

    assert provider.get_secret("connections/provider") == b"secret-bytes"


@pytest.mark.parametrize(
    "reference",
    ["", "/connections/google", "arn:aws:secretsmanager:region:account:secret:x", "../secret"],
)
def test_aws_secret_provider_rejects_unsafe_references(reference):
    provider = AwsSecretsManagerProvider(
        secret_prefix="automation-os/prod/tenant-1",
        client=FakeSecretsManagerClient(),
    )

    with pytest.raises(SecretResolutionError):
        provider.get_secret(reference)


def test_aws_secret_provider_fails_closed_without_secret_material():
    provider = AwsSecretsManagerProvider(
        secret_prefix="automation-os/prod/tenant-1",
        client=FakeSecretsManagerClient(response={}),
    )

    with pytest.raises(
        SecretResolutionError,
        match="returned no secret material",
    ):
        provider.get_secret("connections/google")


def test_aws_secret_provider_sanitizes_aws_client_errors():
    client = FakeSecretsManagerClient(
        error=RuntimeError("secret-value-must-never-appear-in-error")
    )
    provider = AwsSecretsManagerProvider(
        secret_prefix="automation-os/prod/tenant-1",
        client=client,
    )

    with pytest.raises(
        SecretResolutionError,
        match="AWS Secrets Manager secret resolution failed",
    ) as exc_info:
        provider.get_secret("connections/google")

    assert "secret-value-must-never-appear-in-error" not in str(exc_info.value)
