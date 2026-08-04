"""Build and validate explicit, non-recursive deployment manifests."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from utils.hashing import sha256_file
from utils.paths import resolve_within, safe_posix_relative
from workflow.task import validate_identifier

AUTO_FILE_MAX_BYTES = 64 * 1024 * 1024
AUTO_DEPLOYMENT_MAX_BYTES = 256 * 1024 * 1024
DEPLOYMENT_ID_PATTERN = re.compile(r"^DEP-\d{8}-\d{6}$")
SECRET_PATHS = {".env"}
MANUAL_UPLOAD_SUFFIXES = {
    ".ckpt",
    ".gguf",
    ".mkv",
    ".mov",
    ".mp4",
    ".pt",
    ".pth",
    ".safetensors",
}


class TransferMode(StrEnum):
    """Allowed handling for one explicitly named path."""

    AUTO = "auto"
    MANUAL = "manual"
    REMOTE_EXISTING = "remote_existing"
    IGNORE = "ignore"


@dataclass(frozen=True)
class ManifestEntry:
    """One file in a deployment manifest."""

    source_path: str
    remote_path: str
    mode: TransferMode
    size_bytes: int | None = None
    sha256: str | None = None
    expected_remote_sha256: str | None = None

    def __post_init__(self) -> None:
        safe_posix_relative(self.source_path, field="source_path")
        safe_posix_relative(self.remote_path, field="remote_path")
        for name, value in (
            ("sha256", self.sha256),
            ("expected_remote_sha256", self.expected_remote_sha256),
        ):
            if value is not None and (
                len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value)
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must not be negative")

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible mapping."""
        return {
            "source_path": self.source_path,
            "remote_path": self.remote_path,
            "mode": self.mode.value,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "expected_remote_sha256": self.expected_remote_sha256,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ManifestEntry:
        """Create an entry from decoded JSON."""
        return cls(
            source_path=str(value["source_path"]),
            remote_path=str(value["remote_path"]),
            mode=TransferMode(value["mode"]),
            size_bytes=value.get("size_bytes"),
            sha256=value.get("sha256"),
            expected_remote_sha256=value.get("expected_remote_sha256"),
        )


@dataclass(frozen=True)
class DeploymentManifest:
    """An explicit immutable upload plan."""

    deployment_id: str
    project_id: str
    remote_root: str
    entries: tuple[ManifestEntry, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported deployment manifest schema_version")
        if not DEPLOYMENT_ID_PATTERN.fullmatch(self.deployment_id):
            raise ValueError("deployment_id must use DEP-YYYYMMDD-HHMMSS")
        validate_identifier(self.project_id, field_name="project_id")
        remote_root = PurePosixPath(self.remote_root)
        raw_parts = self.remote_root.split("/")[1:]
        if (
            not remote_root.is_absolute()
            or any(part in {"", ".", ".."} for part in raw_parts)
            or remote_root.as_posix() != self.remote_root
        ):
            raise ValueError("remote_root must be a normalized absolute POSIX path")
        if not self.entries:
            raise ValueError("deployment manifest must contain explicit entries")
        remote_paths = [entry.remote_path for entry in self.entries]
        if len(remote_paths) != len(set(remote_paths)):
            raise ValueError("deployment manifest contains duplicate remote paths")
        auto_bytes = sum(
            entry.size_bytes or 0 for entry in self.entries if entry.mode is TransferMode.AUTO
        )
        if auto_bytes > AUTO_DEPLOYMENT_MAX_BYTES:
            raise ValueError("automatic deployment exceeds 256 MiB")

    def as_dict(self) -> dict[str, Any]:
        """Return the canonical JSON representation."""
        return {
            "schema_version": self.schema_version,
            "deployment_id": self.deployment_id,
            "project_id": self.project_id,
            "remote_root": self.remote_root,
            "entries": [entry.as_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DeploymentManifest:
        """Create a manifest from decoded JSON."""
        return cls(
            schema_version=int(value["schema_version"]),
            deployment_id=str(value["deployment_id"]),
            project_id=str(value["project_id"]),
            remote_root=str(value["remote_root"]),
            entries=tuple(ManifestEntry.from_dict(item) for item in value["entries"]),
        )

    @classmethod
    def load(cls, path: Path) -> DeploymentManifest:
        """Load a deployment manifest from disk."""
        with path.open(encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))


def _is_secret_path(path: str) -> bool:
    candidate = safe_posix_relative(path)
    normalized = candidate.as_posix()
    return (
        candidate.parts[0] == ".local"
        or normalized in SECRET_PATHS
        or normalized.startswith(".env.")
    )


def _requires_manual_upload(path: str) -> bool:
    candidate = safe_posix_relative(path)
    return (
        candidate.parts[0] in {"models", "outputs", "deliverables", "runs"}
        or candidate.suffix.lower() in MANUAL_UPLOAD_SUFFIXES
        or candidate.as_posix().startswith("data/references/video/")
    )


def build_manifest(
    *,
    project_root: Path,
    deployment_id: str,
    project_id: str,
    remote_root: str,
    file_specs: Sequence[Mapping[str, Any]],
) -> DeploymentManifest:
    """Build a manifest from an explicit file list without directory discovery."""
    entries: list[ManifestEntry] = []
    for spec in file_specs:
        source = str(spec["source_path"])
        remote = str(spec.get("remote_path", source))
        mode = TransferMode(spec["mode"])
        expected_remote = spec.get("expected_remote_sha256")

        if _is_secret_path(source) or _is_secret_path(remote):
            if mode is not TransferMode.IGNORE:
                raise ValueError(f"secret path must never be transferred: {source}")
        if mode is TransferMode.AUTO and (
            _requires_manual_upload(source) or _requires_manual_upload(remote)
        ):
            raise ValueError(f"source or remote path is manual-only: {source} -> {remote}")

        size: int | None = spec.get("size_bytes")
        digest: str | None = spec.get("sha256")
        if mode in {TransferMode.AUTO, TransferMode.MANUAL}:
            local_path = resolve_within(project_root, source, must_exist=True)
            if local_path.is_symlink() or not local_path.is_file():
                raise ValueError(f"deployment source must be a regular non-symlink file: {source}")
            size = local_path.stat().st_size
            digest = sha256_file(local_path)
            if mode is TransferMode.AUTO and size > AUTO_FILE_MAX_BYTES:
                raise ValueError(f"automatic file exceeds 64 MiB: {source}")
        elif mode is TransferMode.REMOTE_EXISTING and (size is None or digest is None):
            raise ValueError("remote_existing entries require expected size_bytes and sha256")

        entries.append(
            ManifestEntry(
                source_path=source,
                remote_path=remote,
                mode=mode,
                size_bytes=size,
                sha256=digest,
                expected_remote_sha256=expected_remote,
            )
        )

    return DeploymentManifest(
        deployment_id=deployment_id,
        project_id=project_id,
        remote_root=remote_root,
        entries=tuple(entries),
    )


def verify_local_manifest(manifest: DeploymentManifest, project_root: Path) -> None:
    """Recompute local automatic-upload evidence immediately before transfer."""
    for entry in manifest.entries:
        if entry.mode is not TransferMode.AUTO:
            continue
        path = resolve_within(project_root, entry.source_path, must_exist=True)
        if path.stat().st_size != entry.size_bytes or sha256_file(path) != entry.sha256:
            raise ValueError(
                f"deployment source changed after manifest creation: {entry.source_path}"
            )
