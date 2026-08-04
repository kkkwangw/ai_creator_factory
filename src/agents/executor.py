"""Agent execution boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base import AgentContext, AgentResult


class AgentExecutor(ABC):
    """Executes registered agents with runtime policies."""

    @abstractmethod
    def execute(self, agent_name: str, context: AgentContext) -> AgentResult:
        """Execute an agent by name.

        TODO: Add cancellation, timeouts, tracing, and retry policies after semantics are defined.
        """

