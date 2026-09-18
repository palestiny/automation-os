from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Intent:
    """Provider-neutral description of a requested business outcome."""

    goal: str
    parameters: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("Intent goal cannot be empty")

        if not isinstance(self.parameters, Mapping):
            raise ValueError("Intent parameters must be a mapping")

        if any(not isinstance(name, str) for name in self.parameters):
            raise ValueError("Intent parameter names must be strings")

        if any(not name.strip() for name in self.parameters):
            raise ValueError("Intent parameter names cannot be empty")

        object.__setattr__(
            self,
            "goal",
            self.goal.strip(),
        )
        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )

    @classmethod
    def create(
        cls,
        goal: str,
        parameters: Mapping[str, object] | None = None,
    ) -> "Intent":
        return cls(
            goal=goal,
            parameters=parameters or {},
        )
