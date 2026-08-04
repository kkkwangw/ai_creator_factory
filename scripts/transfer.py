#!/usr/bin/env python3
"""Manifest-bound password SSH/SFTP transfer commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from deployment.manifest import DeploymentManifest
from deployment.ssh import SFTPTransport, SSHTarget


def _target(env_file: Path) -> SSHTarget:
    return SSHTarget.from_environment(env_file=env_file)


def _transport(target: SSHTarget, known_hosts: Path) -> SFTPTransport:
    return SFTPTransport(target, known_hosts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=PROJECT_ROOT / ".env")
    parser.add_argument(
        "--known-hosts", type=Path, default=PROJECT_ROOT / ".local" / "known_hosts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init-marker")
    initialize.add_argument("--remote-root", required=True)
    initialize.add_argument("--project-id", required=True)
    initialize.add_argument("--template-version", required=True)
    initialize.add_argument("--confirmed-project-id", required=True)

    upload = subparsers.add_parser("upload")
    upload.add_argument("manifest", type=Path)

    download = subparsers.add_parser("download")
    download.add_argument("spec", type=Path)

    args = parser.parse_args()
    target = _target(args.env_file)
    with _transport(target, args.known_hosts) as transport:
        if args.command == "init-marker":
            if args.confirmed_project_id != args.project_id:
                raise ValueError("explicit project confirmation does not match project_id")
            transport.initialize_project_marker(
                remote_root=args.remote_root,
                project_id=args.project_id,
                template_version=args.template_version,
            )
            result: object = {"initialized": True, "project_id": args.project_id}
        elif args.command == "upload":
            manifest = DeploymentManifest.load(args.manifest)
            result = transport.upload(manifest, PROJECT_ROOT)
        else:
            with args.spec.open(encoding="utf-8") as handle:
                spec = json.load(handle)
            configured_root = Path(spec.get("local_root", "."))
            local_root = (
                configured_root.resolve()
                if configured_root.is_absolute()
                else (PROJECT_ROOT / configured_root).resolve()
            )
            if not local_root.is_relative_to(PROJECT_ROOT):
                raise ValueError("download local_root must remain inside the project")
            result = transport.download(
                remote_root=str(spec["remote_root"]),
                project_id=str(spec["project_id"]),
                local_root=local_root,
                file_specs=spec["files"],
            )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
