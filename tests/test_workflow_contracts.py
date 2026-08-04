"""Tests for exact identity, retry, and Gate invalidation rules."""

import pytest

from workflow.task import (
    Gate,
    RetryPolicy,
    TaskEnvelope,
    TaskIdentity,
    invalidated_gates_from,
)


def test_gate_three_invalidates_three_through_six() -> None:
    assert invalidated_gates_from(Gate.NARRATION) == (
        Gate.NARRATION,
        Gate.CHARACTER_AND_KEYFRAMES,
        Gate.VIDEO_AND_LIPSYNC,
        Gate.COMPOSE_AND_DELIVER,
    )


def test_identifiers_reject_shell_and_path_syntax() -> None:
    for unsafe in ("../run", "run_1", "RUN-1", "run;id", "/run"):
        with pytest.raises(ValueError):
            TaskIdentity(run_id=unsafe, task_id="task-one", prompt_id="prompt-one")


def test_task_envelope_serializes_exact_identity() -> None:
    identity = TaskIdentity("run-one", "task-one", "prompt-one")
    envelope = TaskEnvelope(
        project_id="project-one",
        template_version="0.2.0",
        identity=identity,
        markdown_path="tasks/task-one.md",
        markdown_sha256="a" * 64,
        inputs={"book_title": "Test"},
        retry=RetryPolicy(),
    )

    assert envelope.as_dict()["identity"] == identity.as_dict()
    assert envelope.as_dict()["retry"]["max_attempts"] == 3


def test_retry_attempts_cannot_exceed_three() -> None:
    with pytest.raises(ValueError, match="between 1 and 3"):
        RetryPolicy(max_attempts=4)


def test_task_envelope_rejects_non_hex_markdown_digest() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        TaskEnvelope(
            project_id="project-one",
            template_version="0.2.0",
            identity=TaskIdentity("run-one", "task-one", "prompt-one"),
            markdown_path="tasks/task-one.md",
            markdown_sha256="z" * 64,
        )
