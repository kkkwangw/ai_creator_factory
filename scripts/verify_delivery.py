#!/usr/bin/env python3
"""Verify current delivery files without claiming that all workflow Gates passed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from media.delivery import verify_delivery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    report = verify_delivery(
        project_root=args.project_root.resolve(),
        manifest_path=args.manifest.resolve(),
        ffprobe=args.ffprobe,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
