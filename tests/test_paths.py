"""Tests for project path boundaries."""

from pathlib import Path

import pytest

from utils.paths import UnsafePathError, resolve_within, safe_posix_relative


@pytest.mark.parametrize("value", ["../secret", "/absolute", "a\\b", "a/../b", "./file"])
def test_unsafe_relative_paths_are_rejected(value: str) -> None:
    with pytest.raises(UnsafePathError):
        safe_posix_relative(value)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-target"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafePathError):
        resolve_within(tmp_path, "link/file.txt")
