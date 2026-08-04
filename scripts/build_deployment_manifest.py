#!/usr/bin/env python3
"""Build a deployment manifest from an explicit JSON plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from deployment.manifest import build_manifest


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="Explicit deployment plan JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with args.plan.open(encoding="utf-8") as handle:
        plan = json.load(handle)
    if plan.get("schema_version") != 1:
        raise ValueError("unsupported deployment plan schema_version")
    manifest = build_manifest(
        project_root=PROJECT_ROOT,
        deployment_id=str(plan["deployment_id"]),
        project_id=str(plan["project_id"]),
        remote_root=str(plan["remote_root"]),
        file_specs=plan["files"],
    )
    destination = args.output or (
        PROJECT_ROOT / "deployments" / manifest.deployment_id / "manifest.json"
    )
    destination = destination.resolve()
    if not destination.is_relative_to(PROJECT_ROOT):
        raise ValueError("deployment manifest output must remain inside the project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(manifest.as_dict())
    if destination.exists() and destination.read_bytes() != payload:
        raise ValueError("refusing to overwrite a deployment ID with different content")
    destination.write_bytes(payload)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
