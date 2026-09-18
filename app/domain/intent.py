from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentGoal:
    """Canonical, provider-neutral identifier for a business intent."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Intent goal cannot be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Intent:
    """Provider-neutral description of a requested business outcome."""

    goal: IntentGoal
    parameters: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.goal, IntentGoal):
            raise ValueError("Intent goal must be an IntentGoal instance")

        if not isinstance(self.parameters, Mapping):
            raise ValueError("Intent parameters must be a mapping")

        if any(not isinstance(name, str) for name in self.parameters):
            raise ValueError("Intent parameter names must be strings")

        if any(not name.strip() for name in self.parameters):
            raise ValueError("Intent parameter names cannot be empty")

        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )

    @classmethod
    def create(
        cls,
        goal: str | IntentGoal,
        parameters: Mapping[str, object] | None = None,
    ) -> "Intent":
        return cls(
            goal=goal if isinstance(goal, IntentGoal) else IntentGoal(goal),
            parameters=parameters or {},
        )
