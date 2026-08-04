#!/usr/bin/env python3
"""Compile local task Markdown into an immutable JSON task envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from utils.frontmatter import parse_toml_frontmatter
from utils.hashing import sha256_file
from utils.paths import resolve_within
from workflow.task import RetryPolicy, TaskEnvelope, TaskIdentity

TASK_INPUT_FIELDS = {
    "book_title",
    "author",
    "isbn",
    "recommendation_direction",
    "audience",
    "character_version",
    "visual_template",
}


def canonical_json(value: object) -> bytes:
    """Serialize JSON deterministically for idempotency comparisons."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build(task_relative: str, output: Path | None = None) -> Path:
    """Read project/task frontmatter and write a non-overwritable envelope."""
    policy = json.loads((PROJECT_ROOT / "config/runtime-policy.json").read_text(encoding="utf-8"))
    task_path = resolve_within(PROJECT_ROOT, task_relative, must_exist=True)
    project, _ = parse_toml_frontmatter(PROJECT_ROOT / "PROJECT.md", max_bytes=16384)
    task, _ = parse_toml_frontmatter(
        task_path, max_bytes=int(policy["markdown_limits"]["task_bytes"])
    )
    if project.get("project_status") != "active":
        raise ValueError("task envelopes can only be built in an active actual project")
    if task.get("task_type") != "book_video" or task.get("mode") != "unattended":
        raise ValueError("first version supports only unattended book_video tasks")

    identity = TaskIdentity(
        run_id=str(task["run_id"]),
        task_id=str(task["task_id"]),
        prompt_id=str(task["prompt_id"]),
    )
    inputs = {key: task[key] for key in TASK_INPUT_FIELDS if key in task}
    project_book = str(project.get("book_title", ""))
    if inputs.get("book_title") != project_book:
        raise ValueError("task book_title must match PROJECT.md")

    retry_config = policy["retry"]
    envelope = TaskEnvelope(
        project_id=str(project["project_id"]),
        template_version=str(project["template_version"]),
        identity=identity,
        markdown_path=task_relative,
        markdown_sha256=sha256_file(task_path),
        inputs=inputs,
        retry=RetryPolicy(
            max_attempts=int(retry_config["max_attempts"]),
            task_timeout_minutes=int(retry_config["task_timeout_minutes"]),
            run_gpu_budget_minutes=int(retry_config["run_gpu_budget_minutes"]),
        ),
    )
    destination = output or (
        PROJECT_ROOT
        / "runs"
        / identity.run_id
        / "inputs"
        / f"{identity.task_id}-{identity.prompt_id}.json"
    )
    destination = destination.resolve()
    if not destination.is_relative_to(PROJECT_ROOT):
        raise ValueError("task envelope output must remain inside the project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(envelope.as_dict())
    if destination.exists() and destination.read_bytes() != payload:
        raise ValueError("refusing to overwrite an existing envelope with different content")
    destination.write_bytes(payload)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Task Markdown path relative to the project root")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(build(args.task, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
