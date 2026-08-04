"""Tests for non-recursive, secret-safe deployment manifests."""

from pathlib import Path

import pytest

from deployment.manifest import TransferMode, build_manifest, verify_local_manifest


def test_build_manifest_hashes_only_explicit_file(tmp_path: Path) -> None:
    (tmp_path / "tasks").mkdir()
    source = tmp_path / "tasks" / "task-one.md"
    source.write_text("task", encoding="utf-8")

    manifest = build_manifest(
        project_root=tmp_path,
        deployment_id="DEP-20260804-153000",
        project_id="project-one",
        remote_root="/persistent/project-one",
        file_specs=[
            {
                "source_path": "tasks/task-one.md",
                "remote_path": "tasks/task-one.md",
                "mode": "auto",
            }
        ],
    )

    assert manifest.entries[0].mode is TransferMode.AUTO
    assert manifest.entries[0].size_bytes == 4
    verify_local_manifest(manifest, tmp_path)


def test_secret_file_cannot_be_uploaded(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=value", encoding="utf-8")

    with pytest.raises(ValueError, match="secret path"):
        build_manifest(
            project_root=tmp_path,
            deployment_id="DEP-20260804-153000",
            project_id="project-one",
            remote_root="/persistent/project-one",
            file_specs=[{"source_path": ".env", "mode": "auto"}],
        )


def test_machine_local_directory_cannot_be_uploaded(tmp_path: Path) -> None:
    (tmp_path / ".local").mkdir()
    (tmp_path / ".local" / "project-marker.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="secret path"):
        build_manifest(
            project_root=tmp_path,
            deployment_id="DEP-20260804-153000",
            project_id="project-one",
            remote_root="/persistent/project-one",
            file_specs=[{"source_path": ".local/project-marker.json", "mode": "auto"}],
        )


@pytest.mark.parametrize(
    "remote_root", ["persistent/project-one", "/persistent/../project-one", "/persistent//one"]
)
def test_remote_root_must_be_normalized(remote_root: str, tmp_path: Path) -> None:
    source = tmp_path / "task.json"
    source.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="remote_root"):
        build_manifest(
            project_root=tmp_path,
            deployment_id="DEP-20260804-153000",
            project_id="project-one",
            remote_root=remote_root,
            file_specs=[{"source_path": "task.json", "mode": "auto"}],
        )


def test_video_upload_is_manual_only(tmp_path: Path) -> None:
    (tmp_path / "reference.mp4").write_bytes(b"video")

    with pytest.raises(ValueError, match="manual-only"):
        build_manifest(
            project_root=tmp_path,
            deployment_id="DEP-20260804-153000",
            project_id="project-one",
            remote_root="/persistent/project-one",
            file_specs=[{"source_path": "reference.mp4", "mode": "auto"}],
        )


def test_auto_upload_cannot_map_small_file_into_models(tmp_path: Path) -> None:
    (tmp_path / "small.bin").write_bytes(b"not-a-model")

    with pytest.raises(ValueError, match="manual-only"):
        build_manifest(
            project_root=tmp_path,
            deployment_id="DEP-20260804-153000",
            project_id="project-one",
            remote_root="/persistent/project-one",
            file_specs=[
                {
                    "source_path": "small.bin",
                    "remote_path": "models/small.bin",
                    "mode": "auto",
                }
            ],
        )


def test_changed_file_invalidates_manifest(tmp_path: Path) -> None:
    path = tmp_path / "task.json"
    path.write_text("one", encoding="utf-8")
    manifest = build_manifest(
        project_root=tmp_path,
        deployment_id="DEP-20260804-153000",
        project_id="project-one",
        remote_root="/persistent/project-one",
        file_specs=[{"source_path": "task.json", "mode": "auto"}],
    )
    path.write_text("two", encoding="utf-8")

    with pytest.raises(ValueError, match="changed"):
        verify_local_manifest(manifest, tmp_path)
