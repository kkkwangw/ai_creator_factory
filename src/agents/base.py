"""Base types shared by all agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentContext:
    """Validated input made available to an agent."""

    objective: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    constraints: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class AgentResult:
    """Structured output returned by an agent."""

    content: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: Sequence[str] = field(default_factory=tuple)


class Agent(ABC):
    """Provider-independent agent contract."""

    # TODO: Add capability declarations after the first concrete agent use case.

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable registry name."""

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute one bounded unit of work."""
