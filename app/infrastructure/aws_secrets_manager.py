from __future__ import annotations

import re
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.application.secret_provider import SecretResolutionError

_SECRET_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9/_+=.@-]+$")


class AwsSecretsManagerProvider:
    """AWS Secrets Manager adapter behind the provider-neutral SecretProvider port.

    The provider accepts only a logical reference relative to its configured
    prefix. The caller cannot supply an arbitrary ARN or cross-tenant secret
    identifier. Tenant isolation is established by composing a tenant-scoped
    prefix before this adapter is injected into runtime execution.
    """

    def __init__(
        self,
        *,
        secret_prefix: str,
        client: Any | None = None,
        region_name: str | None = None,
    ) -> None:
        normalized_prefix = secret_prefix.strip().strip("/")
        if not normalized_prefix:
            raise ValueError("AWS secret prefix cannot be empty")
        if not _SECRET_REFERENCE_PATTERN.fullmatch(normalized_prefix):
            raise ValueError("AWS secret prefix contains unsupported characters")

        self._secret_prefix = normalized_prefix
        self._client = client or boto3.client(
            "secretsmanager",
            region_name=region_name,
            config=Config(
                connect_timeout=2,
                read_timeout=5,
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )

    def get_secret(self, secret_reference: str) -> object:
        if not isinstance(secret_reference, str):
            raise SecretResolutionError("AWS secret reference must be text")

        if secret_reference != secret_reference.strip():
            raise SecretResolutionError("AWS secret reference contains surrounding whitespace")
        if secret_reference.startswith("/") or secret_reference.endswith("/"):
            raise SecretResolutionError("AWS secret reference must be relative")
        reference = secret_reference
        if not reference:
            raise SecretResolutionError("AWS secret reference cannot be empty")
        if not _SECRET_REFERENCE_PATTERN.fullmatch(reference):
            raise SecretResolutionError("AWS secret reference contains unsupported characters")
        if reference.startswith("arn:"):
            raise SecretResolutionError("AWS secret reference must be logical, not an ARN")
        if ".." in reference:
            raise SecretResolutionError("AWS secret reference contains an invalid path")

        secret_id = f"{self._secret_prefix}/{reference}"

        try:
            response = self._client.get_secret_value(SecretId=secret_id)
        except (ClientError, BotoCoreError) as exc:
            error_code = self._error_code(exc)
            raise SecretResolutionError(
                f"AWS Secrets Manager secret resolution failed ({error_code})"
            ) from exc
        except Exception as exc:
            raise SecretResolutionError(
                "AWS Secrets Manager secret resolution failed"
            ) from exc

        if "SecretString" in response:
            return response["SecretString"]
        if "SecretBinary" in response:
            return response["SecretBinary"]

        raise SecretResolutionError(
            "AWS Secrets Manager returned no secret material"
        )

    @staticmethod
    def _error_code(exc: BaseException) -> str:
        if isinstance(exc, ClientError):
            return str(
                exc.response.get("Error", {}).get("Code", "ClientError")
            )
        return exc.__class__.__name__
