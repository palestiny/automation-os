from __future__ import annotations

from dataclasses import dataclass


_SUPPORTED_PARAMETER_TYPES = frozenset({"string", "integer", "number", "boolean"})


@dataclass(frozen=True)
class WorkflowCandidateStep:
    """Provider-neutral workflow step proposal without a runtime identity."""

    name: str
    capability: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Workflow candidate step name cannot be empty")
        if not isinstance(self.capability, str) or not self.capability.strip():
            raise ValueError("Workflow candidate step capability cannot be empty")

    @classmethod
    def create(cls, name: str, capability: str) -> "WorkflowCandidateStep":
        return cls(name=name.strip(), capability=capability.strip())


@dataclass(frozen=True)
class WorkflowCandidate:
    """Provider-neutral, unpublishable workflow definition proposed for review."""

    name: str
    supported_goals: tuple[str, ...]
    required_parameters: tuple[str, ...]
    capabilities: tuple[str, ...]
    parameter_types: tuple[tuple[str, str], ...] = ()
    steps: tuple[WorkflowCandidateStep, ...] = ()
    triggers: tuple[str, ...] = ()
    automation_domain: str | None = None
    discovery_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Workflow candidate name cannot be empty")

        for field_name, values in (
            ("supported goals", self.supported_goals),
            ("required parameters", self.required_parameters),
            ("capabilities", self.capabilities),
            ("triggers", self.triggers),
            ("discovery tags", self.discovery_tags),
        ):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(
                    f"Workflow candidate {field_name} must contain non-empty strings"
                )

        if len(set(self.supported_goals)) != len(self.supported_goals):
            raise ValueError("Workflow candidate supported goals must be unique")
        if len(set(self.required_parameters)) != len(self.required_parameters):
            raise ValueError("Workflow candidate required parameters must be unique")

        required_parameters = set(self.required_parameters)
        parameter_names = {name for name, _ in self.parameter_types}
        if not parameter_names.issubset(required_parameters):
            raise ValueError(
                "Workflow candidate parameter types must reference required parameters"
            )
        if len(parameter_names) != len(self.parameter_types):
            raise ValueError("Workflow candidate parameter types must be unique")

        for parameter_name, parameter_type in self.parameter_types:
            if not isinstance(parameter_name, str) or not parameter_name.strip():
                raise ValueError("Workflow candidate parameter names cannot be empty")
            if parameter_type not in _SUPPORTED_PARAMETER_TYPES:
                raise ValueError(
                    f"Unsupported workflow candidate parameter type: {parameter_type}"
                )

        if any(not isinstance(step, WorkflowCandidateStep) for step in self.steps):
            raise TypeError("Workflow candidate steps must be WorkflowCandidateStep instances")

        if self.automation_domain is not None and (
            not isinstance(self.automation_domain, str) or not self.automation_domain.strip()
        ):
            raise ValueError("Workflow candidate automation domain cannot be empty")

    @classmethod
    def create(
        cls,
        name: str,
        supported_goals: list[str],
        required_parameters: list[str] | None = None,
        capabilities: list[str] | None = None,
        parameter_types: dict[str, str] | None = None,
        steps: list[WorkflowCandidateStep] | None = None,
        triggers: list[str] | None = None,
        automation_domain: str | None = None,
        discovery_tags: list[str] | None = None,
    ) -> "WorkflowCandidate":
        normalized_steps = tuple(steps or [])
        normalized_capabilities = (
            tuple(capability.strip() for capability in capabilities)
            if capabilities is not None
            else tuple(step.capability.strip() for step in normalized_steps)
        )
        normalized_parameter_types = tuple(
            (parameter_name.strip(), parameter_type.strip())
            for parameter_name, parameter_type in (parameter_types or {}).items()
        )

        if steps is not None and not normalized_steps:
            raise ValueError("Workflow candidate must contain at least one step")

        return cls(
            name=name.strip(),
            supported_goals=tuple(goal.strip() for goal in supported_goals),
            required_parameters=tuple(
                parameter.strip() for parameter in (required_parameters or [])
            ),
            capabilities=normalized_capabilities,
            parameter_types=normalized_parameter_types,
            steps=normalized_steps,
            triggers=tuple(trigger.strip() for trigger in (triggers or [])),
            automation_domain=(
                automation_domain.strip() if automation_domain is not None else None
            ),
            discovery_tags=tuple(tag.strip() for tag in (discovery_tags or [])),
        )
