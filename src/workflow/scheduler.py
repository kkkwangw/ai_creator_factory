"""Workflow scheduling boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from workflow.task import Task, TaskIdentity


class WorkflowScheduler(ABC):
    """Plans when workflow tasks become eligible for execution."""

    @abstractmethod
    def submit(self, tasks: Sequence[Task], run_at: datetime | None = None) -> str:
        """Schedule tasks and return a run identifier.

        TODO: Replace the optional value with a schedule value object when needed.
        """

    @abstractmethod
    def cancel(self, identity: TaskIdentity) -> None:
        """Request exact cancellation for one run/task/prompt identity."""
