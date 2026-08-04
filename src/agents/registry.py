"""Agent registration boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from agents.base import Agent


class AgentRegistry(ABC):
    """Stores and resolves agents by stable name."""

    # TODO: Define versioning and replacement behavior before implementation.

    @abstractmethod
    def register(self, agent: Agent) -> None:
        """Register one agent, rejecting duplicate names."""

    @abstractmethod
    def get(self, name: str) -> Agent:
        """Resolve a registered agent."""

    @abstractmethod
    def list(self) -> Sequence[Agent]:
        """Return all registered agents."""
