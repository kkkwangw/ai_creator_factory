"""Tests for read-only TOML frontmatter parsing."""

from pathlib import Path

import pytest

from utils.frontmatter import FrontmatterError, parse_toml_frontmatter


def test_parse_toml_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "task.md"
    path.write_text(
        '+++\nschema_version = 1\nbook_title = "Test"\n+++\n\n# Body\n',
        encoding="utf-8",
    )

    metadata, body = parse_toml_frontmatter(path)

    assert metadata == {"schema_version": 1, "book_title": "Test"}
    assert body == "# Body"


def test_frontmatter_size_limit_is_enforced(tmp_path: Path) -> None:
    path = tmp_path / "task.md"
    path.write_text("+++\na = 1\n+++\n", encoding="utf-8")

    with pytest.raises(FrontmatterError, match="exceeds"):
        parse_toml_frontmatter(path, max_bytes=1)
