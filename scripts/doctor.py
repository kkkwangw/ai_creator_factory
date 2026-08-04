#!/usr/bin/env python3
"""Read-only local or remote runtime inspection; never installs or repairs tools."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from _bootstrap import PROJECT_ROOT


def _load_tools(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _resolve_command(configured: str | None, fallback: str) -> str | None:
    if configured:
        path = Path(configured)
        return str(path) if path.is_file() else None
    return shutil.which(fallback)


def _probe(command: str | None, arguments: list[str]) -> dict[str, Any]:
    if command is None:
        return {"available": False}
    result = subprocess.run(
        [command, *arguments], check=False, capture_output=True, text=True, timeout=20
    )
    output = (result.stdout or result.stderr).strip().splitlines()
    return {
        "available": result.returncode == 0,
        "path": command,
        "summary": output[0][:300] if output else "",
    }


def inspect(mode: str, tools_path: Path) -> dict[str, Any]:
    tools = _load_tools(tools_path)
    section = tools.get(mode, {})
    report: dict[str, Any] = {
        "schema_version": 1,
        "mode": mode,
        "python": {
            "version": sys.version.split()[0],
            "is_3_11": sys.version_info[:2] == (3, 11),
            "conda_environment": os.environ.get("CONDA_DEFAULT_ENV", ""),
        },
    }
    report["ffmpeg"] = _probe(_resolve_command(section.get("ffmpeg"), "ffmpeg"), ["-version"])
    report["ffprobe"] = _probe(_resolve_command(section.get("ffprobe"), "ffprobe"), ["-version"])
    if mode == "local":
        report["whisper"] = _probe(
            _resolve_command(section.get("whisper"), "whisper-cli"), ["--help"]
        )
    else:
        report["uv"] = _probe(_resolve_command(section.get("uv"), "uv"), ["--version"])
        report["nvidia_smi"] = _probe(
            shutil.which("nvidia-smi"),
            ["--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
        )
        persistent_root = str(section.get("persistent_root", ""))
        if persistent_root and Path(persistent_root).is_dir():
            usage = shutil.disk_usage(persistent_root)
            report["persistent_disk"] = {"path": persistent_root, "free_bytes": usage.free}
        else:
            report["persistent_disk"] = {"path": persistent_root, "available": False}
        comfy_url = str(section.get("comfyui_url", ""))
        report["comfyui_loopback_only"] = comfy_url.startswith(
            ("http://127.0.0.1:", "http://localhost:")
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local", "remote"], default="local")
    parser.add_argument("--tools", type=Path, default=PROJECT_ROOT / ".local" / "tools.toml")
    args = parser.parse_args()
    report = inspect(args.mode, args.tools)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["python"]["is_3_11"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
