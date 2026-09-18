from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class BusinessData:
    values: dict[str, object]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("BusinessData values cannot be empty")
        if any(not isinstance(key, str) or not key.strip() for key in self.values):
            raise ValueError("BusinessData keys must be non-empty strings")

    @classmethod
    def create(cls, values: dict[str, object]) -> "BusinessData":
        return cls(values=dict(values))


@dataclass(frozen=True)
class ReportSpecification:
    name: str
    format: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ReportSpecification name cannot be empty")
        if not self.format.strip():
            raise ValueError("ReportSpecification format cannot be empty")

    @classmethod
    def create(cls, name: str, format: str) -> "ReportSpecification":
        return cls(name=name.strip(), format=format.strip())


@dataclass(frozen=True)
class ReportAsset:
    id: UUID
    specification: ReportSpecification
    reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.specification, ReportSpecification):
            raise ValueError("ReportAsset specification must be a ReportSpecification instance")
        if not self.reference.strip():
            raise ValueError("ReportAsset reference cannot be empty")

    @classmethod
    def create(cls, specification: ReportSpecification, reference: str) -> "ReportAsset":
        return cls(id=uuid4(), specification=specification, reference=reference)
