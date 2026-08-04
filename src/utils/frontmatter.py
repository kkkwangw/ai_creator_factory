"""Read-only TOML frontmatter parsing for project and task Markdown."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


class FrontmatterError(ValueError):
    """Raised when Markdown frontmatter is missing or malformed."""


def parse_toml_frontmatter(
    path: Path, *, max_bytes: int | None = None
) -> tuple[dict[str, Any], str]:
    """Parse `+++` TOML frontmatter without modifying the Markdown file."""
    size = path.stat().st_size
    if max_bytes is not None and size > max_bytes:
        raise FrontmatterError(f"{path} exceeds {max_bytes} bytes")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        raise FrontmatterError(f"{path} must start with TOML frontmatter delimiter +++")

    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "+++"
        )
    except StopIteration as error:
        raise FrontmatterError(f"{path} is missing the closing +++ delimiter") from error

    try:
        metadata = tomllib.loads("\n".join(lines[1:closing]))
    except tomllib.TOMLDecodeError as error:
        raise FrontmatterError(f"invalid TOML frontmatter in {path}: {error}") from error

    return metadata, "\n".join(lines[closing + 1 :]).lstrip()
