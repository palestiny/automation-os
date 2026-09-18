from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowCandidate:
    """Provider-neutral, unpublishable workflow definition proposed for review."""

    name: str
    supported_goals: tuple[str, ...]
    required_parameters: tuple[str, ...]
    capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Workflow candidate name cannot be empty")
        for field_name, values in (
            ("supported goals", self.supported_goals),
            ("required parameters", self.required_parameters),
            ("capabilities", self.capabilities),
        ):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"Workflow candidate {field_name} must contain non-empty strings")
        if len(set(self.supported_goals)) != len(self.supported_goals):
            raise ValueError("Workflow candidate supported goals must be unique")
        if len(set(self.required_parameters)) != len(self.required_parameters):
            raise ValueError("Workflow candidate required parameters must be unique")

    @classmethod
    def create(
        cls,
        name: str,
        supported_goals: list[str],
        required_parameters: list[str] | None = None,
        capabilities: list[str] | None = None,
    ) -> "WorkflowCandidate":
        return cls(
            name=name.strip(),
            supported_goals=tuple(goal.strip() for goal in supported_goals),
            required_parameters=tuple(
                parameter.strip() for parameter in (required_parameters or [])
            ),
            capabilities=tuple(
                capability.strip() for capability in (capabilities or [])
            ),
        )
