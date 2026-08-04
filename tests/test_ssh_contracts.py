"""Tests for transfer path boundaries that do not require an SSH server."""

import pytest

from deployment.ssh import validate_download_paths


def test_result_download_paths_are_allowed() -> None:
    remote, local = validate_download_paths(
        "runs/run-one/evidence/gate-5.json",
        "runs/run-one/evidence/gate-5.json",
    )

    assert remote.as_posix() == local.as_posix()


@pytest.mark.parametrize(
    ("remote", "local"),
    [
        ("PROJECT.md", "PROJECT.md"),
        ("tasks/task-one.md", "tasks/task-one.md"),
        ("memory/CURRENT.md", "memory/CURRENT.md"),
        ("models/wan.bin", "models/wan.bin"),
        ("runs/run-one/result.json", "TODO.md"),
    ],
)
def test_download_cannot_overwrite_control_or_model_paths(remote: str, local: str) -> None:
    with pytest.raises(ValueError, match="result namespaces|deliverables, outputs, or runs"):
        validate_download_paths(remote, local)
