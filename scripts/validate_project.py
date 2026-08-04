#!/usr/bin/env python3
"""Validate project control files without modifying Markdown or local secrets."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from _bootstrap import PROJECT_ROOT
from utils.frontmatter import FrontmatterError, parse_toml_frontmatter
from utils.hashing import sha256_file
from workflow.task import validate_identifier


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _validate_weread_bundle(root: Path, errors: list[str]) -> None:
    bundle = root / ".agents" / "skills" / "weread-skills"
    source_path = bundle / "SOURCE.json"
    provider_path = root / "config" / "providers" / "weread.json"
    try:
        source = _read_json(source_path)
        provider = _read_json(provider_path)
    except (OSError, ValueError) as error:
        errors.append(f"invalid vendored WeRead metadata: {error}")
        return

    for field in ("skill_version", "source_commit"):
        if source.get(field) != provider.get(field):
            errors.append(f"vendored WeRead {field} does not match provider policy")

    expected = source.get("file_sha256")
    if not isinstance(expected, dict) or not expected:
        errors.append("vendored WeRead SOURCE.json has no file hash inventory")
        return
    actual_names = {
        path.name for path in bundle.iterdir() if path.is_file() and path.name != "SOURCE.json"
    }
    if actual_names != set(expected):
        errors.append("vendored WeRead file inventory differs from SOURCE.json")
        return
    for name, digest in expected.items():
        if sha256_file(bundle / name) != digest:
            errors.append(f"vendored WeRead hash mismatch: {name}")


def validate(root: Path) -> dict[str, Any]:
    """Return a structured validation report for a template or actual project."""
    policy = _read_json(root / "config" / "runtime-policy.json")
    limits = policy["markdown_limits"]
    errors: list[str] = []
    warnings: list[str] = []
    _validate_weread_bundle(root, errors)

    checks = {
        "TODO.md": int(limits["todo_bytes"]),
        "memory/CURRENT.md": int(limits["current_bytes"]),
    }
    for relative, maximum in checks.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing control file: {relative}")
        elif path.stat().st_size > maximum:
            errors.append(f"{relative} exceeds {maximum} bytes")

    try:
        todo, _ = parse_toml_frontmatter(root / "TODO.md", max_bytes=int(limits["todo_bytes"]))
    except (OSError, FrontmatterError) as error:
        errors.append(str(error))
        todo = {}
    current_task_id = str(todo.get("current_task_id", ""))
    current_run_id = str(todo.get("current_run_id", ""))
    for field_name, value in (
        ("current_task_id", current_task_id),
        ("current_run_id", current_run_id),
    ):
        if value:
            try:
                validate_identifier(value, field_name=field_name)
            except ValueError as error:
                errors.append(str(error))
    if current_task_id and not (root / "tasks" / f"{current_task_id}.md").is_file():
        errors.append("TODO.md current_task_id has no matching task Markdown")

    history = sorted((root / "memory" / "history").glob("*.md"))
    if len(history) > int(policy["storage"]["memory_history_limit"]):
        errors.append("memory history exceeds 20 Markdown snapshots")
    for path in history:
        if path.stat().st_size > int(limits["history_item_bytes"]):
            errors.append(f"history snapshot exceeds limit: {path.name}")

    for path in sorted((root / "tasks").glob("*.md")):
        if path.name in {"README.md", "example-task.md"}:
            continue
        if path.stat().st_size > int(limits["task_bytes"]):
            errors.append(f"task exceeds limit: {path.name}")

    try:
        project, _ = parse_toml_frontmatter(root / "PROJECT.md", max_bytes=16384)
    except (OSError, FrontmatterError) as error:
        errors.append(str(error))
        project = {}

    status = str(project.get("project_status", ""))
    project_id = str(project.get("project_id", ""))
    if status == "template":
        warnings.append("template is not initialized as an actual project")
    elif status == "active":
        try:
            validate_identifier(project_id, field_name="project_id")
        except ValueError as error:
            errors.append(str(error))
        if not str(project.get("book_title", "")).strip():
            errors.append("active project requires book_title")
        marker_path = root / ".local" / "project-marker.json"
        if not marker_path.is_file():
            errors.append("active project requires .local/project-marker.json")
        else:
            marker = _read_json(marker_path)
            if marker.get("project_id") != project_id:
                errors.append("local project marker does not match PROJECT.md")
    else:
        errors.append("project_status must be template or active")

    tools_path = root / ".local" / "tools.toml"
    if tools_path.exists():
        with tools_path.open("rb") as handle:
            tools = tomllib.load(handle)
        comfy_url = str(tools.get("remote", {}).get("comfyui_url", ""))
        if comfy_url and not (
            comfy_url.startswith("http://127.0.0.1:") or comfy_url.startswith("http://localhost:")
        ):
            errors.append("ComfyUI URL must be loopback-only")

    model_config = _read_json(root / "config" / "models" / "candidates.json")
    if model_config.get("approved"):
        warnings.append("approved model list is non-empty; verify real GPU benchmark evidence")

    return {
        "schema_version": 1,
        "ok": not errors,
        "project_status": status,
        "project_id": project_id,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PROJECT_ROOT
    report = validate(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
