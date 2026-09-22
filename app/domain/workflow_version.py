from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.workflow import (
    Condition,
    Trigger,
    Workflow,
    WorkflowParameter,
    WorkflowState,
    WorkflowStep,
)


@dataclass
class WorkflowVersion:
    """Immutable executable revision of a logical Workflow once published."""

    id: UUID
    workflow_id: UUID
    tenant_id: UUID | None = None
    version_number: int
    name: str
    _steps: list[WorkflowStep]
    state: WorkflowState
    _triggers: list[Trigger] = field(default_factory=list)
    _supported_goals: tuple[str, ...] = ()
    _required_parameters: tuple[str, ...] = ()
    _parameter_types: tuple[WorkflowParameter, ...] = ()
    _automation_domain: str | None = None
    _discovery_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.tenant_id is not None and not isinstance(self.tenant_id, UUID):
            raise ValueError("Workflow version tenant_id must be a UUID or None")
        if self.version_number < 1:
            raise ValueError("Workflow version number must be at least 1")
        if not self.name.strip():
            raise ValueError("Workflow version name cannot be empty")
        if any(not isinstance(step, WorkflowStep) for step in self._steps):
            raise ValueError("Workflow version steps must be WorkflowStep instances")
        if any(not isinstance(trigger, Trigger) for trigger in self._triggers):
            raise ValueError("Workflow version triggers must be Trigger instances")
        if any(not isinstance(goal, str) or not goal.strip() for goal in self._supported_goals):
            raise ValueError("Workflow version supported goals must be non-empty strings")
        if len(set(self._supported_goals)) != len(self._supported_goals):
            raise ValueError("Workflow version supported goals must be unique")
        if any(not isinstance(parameter, str) or not parameter.strip() for parameter in self._required_parameters):
            raise ValueError("Workflow version required parameters must be non-empty strings")
        if len(set(self._required_parameters)) != len(self._required_parameters):
            raise ValueError("Workflow version required parameters must be unique")
        if any(not isinstance(parameter, WorkflowParameter) for parameter in self._parameter_types):
            raise ValueError("Workflow version parameter types must be WorkflowParameter instances")
        parameter_names = {parameter.name for parameter in self._parameter_types}
        if not parameter_names.issubset(set(self._required_parameters)):
            raise ValueError("Workflow version parameter types must reference required parameters")
        if len(parameter_names) != len(self._parameter_types):
            raise ValueError("Workflow version parameter types must be unique")
        if self._automation_domain is not None and (
            not isinstance(self._automation_domain, str) or not self._automation_domain.strip()
        ):
            raise ValueError("Workflow version automation domain must be a non-empty string")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self._discovery_tags):
            raise ValueError("Workflow version discovery tags must be non-empty strings")
        if len(set(self._discovery_tags)) != len(self._discovery_tags):
            raise ValueError("Workflow version discovery tags must be unique")

    @classmethod
    def create_from_workflow(
        cls,
        workflow: Workflow,
        version_number: int,
        version_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> "WorkflowVersion":
        return cls(
            id=version_id or uuid4(),
            workflow_id=workflow.id,
            tenant_id=tenant_id,
            version_number=version_number,
            name=workflow.name,
            _steps=list(workflow.steps),
            state=WorkflowState.DRAFT,
            _triggers=list(workflow.triggers),
            _supported_goals=workflow.supported_goals,
            _required_parameters=workflow.required_parameters,
            _parameter_types=workflow.parameter_types,
            _automation_domain=workflow.automation_domain,
            _discovery_tags=workflow.discovery_tags,
        )

    @classmethod
    def create_from_version(
        cls,
        source: "WorkflowVersion",
        version_number: int,
        version_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> "WorkflowVersion":
        if source.state is not WorkflowState.PUBLISHED:
            raise ValueError("Only a published Workflow version can be cloned")
        return cls(
            id=version_id or uuid4(),
            workflow_id=source.workflow_id,
            tenant_id=tenant_id if tenant_id is not None else source.tenant_id,
            version_number=version_number,
            name=source.name,
            _steps=list(source.steps),
            state=WorkflowState.DRAFT,
            _triggers=list(source.triggers),
            _supported_goals=source.supported_goals,
            _required_parameters=source.required_parameters,
            _parameter_types=source.parameter_types,
            _automation_domain=source.automation_domain,
            _discovery_tags=source.discovery_tags,
        )

    @property
    def steps(self) -> tuple[WorkflowStep, ...]:
        return tuple(self._steps)

    @property
    def triggers(self) -> tuple[Trigger, ...]:
        return tuple(self._triggers)

    @property
    def supported_goals(self) -> tuple[str, ...]:
        return self._supported_goals

    @property
    def required_parameters(self) -> tuple[str, ...]:
        return self._required_parameters

    @property
    def parameter_types(self) -> tuple[WorkflowParameter, ...]:
        return self._parameter_types

    @property
    def automation_domain(self) -> str | None:
        return self._automation_domain

    @property
    def discovery_tags(self) -> tuple[str, ...]:
        return self._discovery_tags

    def publish(self) -> None:
        if self.state is not WorkflowState.DRAFT:
            raise ValueError("Workflow version can only be published from DRAFT state")
        if not self._steps:
            raise ValueError("Workflow version must have at least one step before publishing")
        self.state = WorkflowState.PUBLISHED

    def add_step(self, step: WorkflowStep) -> None:
        if self.state is not WorkflowState.DRAFT:
            raise ValueError("Steps can only be added to a Workflow version in DRAFT state")
        self._steps.append(step)

    def add_trigger(self, trigger: Trigger) -> None:
        if self.state is not WorkflowState.DRAFT:
            raise ValueError("Triggers can only be added to a Workflow version in DRAFT state")
        self._triggers.append(trigger)
