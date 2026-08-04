"""Workflow orchestration boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from workflow.task import Task, TaskResult


class WorkflowEngine(ABC):
    """Executes provider-neutral task graphs."""

    @abstractmethod
    def validate(self, tasks: Sequence[Task]) -> None:
        """Validate task identities, dependencies, and capabilities."""

    @abstractmethod
    def run(self, tasks: Sequence[Task]) -> Sequence[TaskResult]:
        """Execute a validated task graph.

        TODO: Define persistence, resumption, cancellation, and partial failure policies.
        """

