"""Versioned task identities, envelopes, states, and Gate invalidation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any
from uuid import uuid4

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_identifier(value: str, *, field_name: str) -> str:
    """Validate an identifier that is safe for paths and fixed remote commands."""
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must match {IDENTIFIER_PATTERN.pattern}")
    return value


class TaskStatus(StrEnum):
    """Observable task states; evidence remains the completion authority."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    READY_FOR_DOWNLOAD = "ready_for_download"


class Gate(IntEnum):
    """Fixed first-version book-video Gates."""

    BOOK_SOURCE = 1
    SCRIPT_AND_SHOTS = 2
    NARRATION = 3
    CHARACTER_AND_KEYFRAMES = 4
    VIDEO_AND_LIPSYNC = 5
    COMPOSE_AND_DELIVER = 6


def invalidated_gates_from(gate: Gate | int) -> tuple[Gate, ...]:
    """Return the strict N-through-6 invalidation set."""
    start = Gate(gate)
    return tuple(Gate(number) for number in range(start.value, Gate.COMPOSE_AND_DELIVER + 1))


@dataclass(frozen=True)
class TaskIdentity:
    """Exact identity required for submission, query, and cancellation."""

    run_id: str
    task_id: str
    prompt_id: str

    def __post_init__(self) -> None:
        validate_identifier(self.run_id, field_name="run_id")
        validate_identifier(self.task_id, field_name="task_id")
        validate_identifier(self.prompt_id, field_name="prompt_id")

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-compatible identity mapping."""
        return {"run_id": self.run_id, "task_id": self.task_id, "prompt_id": self.prompt_id}


@dataclass(frozen=True)
class RetryPolicy:
    """Hard first-version retry and compute limits."""

    max_attempts: int = 3
    task_timeout_minutes: int = 45
    run_gpu_budget_minutes: int = 240

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3")
        if self.task_timeout_minutes <= 0 or self.run_gpu_budget_minutes <= 0:
            raise ValueError("timeouts and budgets must be positive")


@dataclass(frozen=True)
class TaskEnvelope:
    """Immutable structured input compiled from local task Markdown."""

    project_id: str
    template_version: str
    identity: TaskIdentity
    markdown_path: str
    markdown_sha256: str
    task_type: str = "book_video"
    mode: str = "unattended"
    inputs: Mapping[str, Any] = field(default_factory=dict)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    schema_version: int = 1

    def __post_init__(self) -> None:
        validate_identifier(self.project_id, field_name="project_id")
        if self.schema_version != 1:
            raise ValueError("unsupported task envelope schema_version")
        if self.task_type != "book_video" or self.mode != "unattended":
            raise ValueError("first version supports only unattended book_video tasks")
        if len(self.markdown_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.markdown_sha256
        ):
            raise ValueError("markdown_sha256 must be a SHA-256 hex digest")
        try:
            json.dumps(self.inputs, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as error:
            raise ValueError("task inputs must be JSON serializable") from error

    def as_dict(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible representation."""
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "template_version": self.template_version,
            "identity": self.identity.as_dict(),
            "task_type": self.task_type,
            "mode": self.mode,
            "markdown_path": self.markdown_path,
            "markdown_sha256": self.markdown_sha256,
            "inputs": dict(self.inputs),
            "retry": {
                "max_attempts": self.retry.max_attempts,
                "task_timeout_minutes": self.retry.task_timeout_minutes,
                "run_gpu_budget_minutes": self.retry.run_gpu_budget_minutes,
            },
        }


@dataclass(frozen=True)
class Task:
    """Provider-neutral unit retained for future in-process workflow engines."""

    name: str
    capability: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    dependencies: Sequence[str] = field(default_factory=tuple)
    task_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        validate_identifier(self.task_id, field_name="task_id")


@dataclass(frozen=True)
class TaskResult:
    """Structured execution result; referenced artifacts remain authoritative."""

    identity: TaskIdentity
    status: TaskStatus
    attempt_id: str
    artifacts: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    evidence: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    error_code: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        validate_identifier(self.attempt_id, field_name="attempt_id")
