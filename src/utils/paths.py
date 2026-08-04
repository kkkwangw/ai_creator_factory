"""Strict path validation for local and remote project boundaries."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


class UnsafePathError(ValueError):
    """Raised when a path can escape or ambiguously address the project."""


def safe_posix_relative(value: str, *, field: str = "path") -> PurePosixPath:
    """Validate and return a normalized POSIX relative path."""
    if not value or "\\" in value or "\x00" in value:
        raise UnsafePathError(f"{field} must be a non-empty POSIX path")

    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise UnsafePathError(f"unsafe {field}: {value}")

    candidate = PurePosixPath(value)
    if candidate.is_absolute():
        raise UnsafePathError(f"unsafe {field}: {value}")
    return candidate


def resolve_within(root: Path, relative: str, *, must_exist: bool = False) -> Path:
    """Resolve a relative path and reject project-root or symlink escape."""
    safe = safe_posix_relative(relative)
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved.joinpath(*safe.parts)
    resolved = candidate.resolve(strict=must_exist)
    if not resolved.is_relative_to(root_resolved):
        raise UnsafePathError(f"path escapes project root: {relative}")
    return resolved
