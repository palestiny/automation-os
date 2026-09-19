from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfiguration:
    """Infrastructure configuration for an external provider."""

    provider_id: str
    service_id: str
    endpoint: str | None = None
    credentials_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")
        if not isinstance(self.service_id, str) or not self.service_id.strip():
            raise ValueError("service_id must be a non-empty string")
        if self.endpoint is not None and (
            not isinstance(self.endpoint, str) or not self.endpoint.strip()
        ):
            raise ValueError("endpoint must be a non-empty string when provided")
        if self.credentials_ref is not None and (
            not isinstance(self.credentials_ref, str)
            or not self.credentials_ref.strip()
        ):
            raise ValueError(
                "credentials_ref must be a non-empty string when provided"
            )

    @property
    def provider(self) -> str:
        return self.provider_id.strip()

    @property
    def service(self) -> str:
        return self.service_id.strip()
