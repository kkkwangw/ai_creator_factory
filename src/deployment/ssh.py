"""Optional Paramiko SFTP transport constrained by deployment manifests."""

from __future__ import annotations

import json
import os
import shutil
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from deployment.manifest import DeploymentManifest, TransferMode, verify_local_manifest
from utils.hashing import sha256_file
from utils.paths import resolve_within, safe_posix_relative


class SSHConfigurationError(ValueError):
    """Raised when local SSH configuration is absent or unsafe."""


def load_env_file(path: Path) -> dict[str, str]:
    """Read a strict local KEY=VALUE file without exporting or logging values."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SSHConfigurationError(f"invalid .env line {number}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


@dataclass(frozen=True)
class SSHTarget:
    """Password-authenticated SSH endpoint loaded from local secrets."""

    host: str
    port: int
    username: str
    password: str

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        env_file: Path | None = None,
    ) -> SSHTarget:
        """Load an endpoint without exposing values in command arguments."""
        values = dict(load_env_file(env_file)) if env_file is not None else {}
        values.update(dict(os.environ if environ is None else environ))
        required = ["AICF_SSH_HOST", "AICF_SSH_USERNAME", "AICF_SSH_PASSWORD"]
        missing = [key for key in required if not values.get(key)]
        if missing:
            raise SSHConfigurationError(f"missing local SSH settings: {', '.join(missing)}")
        port = int(values.get("AICF_SSH_PORT", "22"))
        if not 1 <= port <= 65535:
            raise SSHConfigurationError("AICF_SSH_PORT is outside 1..65535")
        return cls(
            host=values["AICF_SSH_HOST"],
            port=port,
            username=values["AICF_SSH_USERNAME"],
            password=values["AICF_SSH_PASSWORD"],
        )


def _paramiko() -> Any:
    try:
        import paramiko
    except ImportError as error:
        raise RuntimeError(
            "Paramiko is optional; install the project [ssh] extra only in Conda codex"
        ) from error
    return paramiko


def validate_download_paths(
    remote_path: str, local_path: str
) -> tuple[PurePosixPath, PurePosixPath]:
    """Limit automatic downloads to result namespaces inside the project."""
    remote_relative = safe_posix_relative(remote_path, field="remote_path")
    local_relative = safe_posix_relative(local_path, field="local_path")
    allowed_result_roots = {"deliverables", "outputs", "runs"}
    if (
        remote_relative.parts[0] not in allowed_result_roots
        or local_relative.parts[0] not in allowed_result_roots
    ):
        raise ValueError(
            "automatic download paths must remain under deliverables, outputs, or runs"
        )
    return remote_relative, local_relative


class SFTPTransport:
    """TOFU SSH/SFTP transport with explicit-file upload and download methods."""

    def __init__(self, target: SSHTarget, known_hosts: Path) -> None:
        self._target = target
        self._known_hosts = known_hosts
        self._client: Any = None
        self._sftp: Any = None

    def __enter__(self) -> SFTPTransport:
        paramiko = _paramiko()
        self._known_hosts.parent.mkdir(parents=True, exist_ok=True)
        client = paramiko.SSHClient()
        if self._known_hosts.exists():
            client.load_host_keys(str(self._known_hosts))
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self._target.host,
            port=self._target.port,
            username=self._target.username,
            password=self._target.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=20,
            auth_timeout=20,
            banner_timeout=20,
        )
        client.save_host_keys(str(self._known_hosts))
        self._client = client
        self._sftp = client.open_sftp()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._sftp is not None:
            self._sftp.close()
        if self._client is not None:
            self._client.close()

    def _require_sftp(self) -> Any:
        if self._sftp is None:
            raise RuntimeError("SFTP transport is not connected")
        return self._sftp

    @staticmethod
    def _remote_path(root: str, relative: str) -> str:
        safe = safe_posix_relative(relative)
        return str(PurePosixPath(root).joinpath(safe))

    def _validate_remote_root(self, remote_root: str) -> None:
        if remote_root in {"/", "/root", "/tmp"}:
            raise ValueError("refusing broad or temporary remote project root")
        root = PurePosixPath(remote_root)
        raw_parts = remote_root.split("/")[1:]
        if (
            not root.is_absolute()
            or any(part in {"", ".", ".."} for part in raw_parts)
            or root.as_posix() != remote_root
        ):
            raise ValueError("remote project root must be a normalized absolute POSIX path")
        attributes = self._require_sftp().lstat(remote_root)
        if stat.S_ISLNK(attributes.st_mode) or not stat.S_ISDIR(attributes.st_mode):
            raise ValueError("remote project root must be a real directory")

    def _read_json(self, remote_path: str) -> Mapping[str, Any]:
        sftp = self._require_sftp()
        with sftp.file(remote_path, "r") as handle:
            return json.loads(handle.read().decode("utf-8"))

    def verify_project_marker(self, remote_root: str, project_id: str) -> None:
        """Reject a remote root whose marker does not match the local project."""
        self._validate_remote_root(remote_root)
        marker_path = str(PurePosixPath(remote_root) / ".local" / "project-marker.json")
        marker = self._read_json(marker_path)
        if marker.get("project_id") != project_id:
            raise ValueError("remote project marker does not match project_id")

    def initialize_project_marker(
        self, *, remote_root: str, project_id: str, template_version: str
    ) -> None:
        """Create the marker only after the caller explicitly confirms the exact root and ID."""
        sftp = self._require_sftp()
        self._validate_remote_root(remote_root)
        marker_dir = str(PurePosixPath(remote_root) / ".local")
        try:
            attributes = sftp.lstat(marker_dir)
            if stat.S_ISLNK(attributes.st_mode) or not stat.S_ISDIR(attributes.st_mode):
                raise ValueError("remote .local is not a safe directory")
        except OSError:
            sftp.mkdir(marker_dir)
        marker_path = str(PurePosixPath(marker_dir) / "project-marker.json")
        try:
            existing = self._read_json(marker_path)
        except OSError:
            existing = None
        if existing is not None:
            if existing.get("project_id") != project_id:
                raise ValueError("existing remote marker belongs to another project")
            return
        payload = {
            "schema_version": 1,
            "project_id": project_id,
            "template_version": template_version,
        }
        temporary = f"{marker_path}.part-{uuid4().hex}"
        with sftp.file(temporary, "w") as handle:
            handle.write((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        sftp.rename(temporary, marker_path)

    def _replace_remote_file(self, temporary: str, destination: str) -> None:
        """Atomically replace a file; block if the server lacks the POSIX extension."""
        sftp = self._require_sftp()
        try:
            sftp.posix_rename(temporary, destination)
        except OSError as error:
            try:
                sftp.remove(temporary)
            except OSError:
                pass
            raise RuntimeError(
                "remote SFTP server does not support atomic POSIX rename"
            ) from error

    def _ensure_remote_parent(self, remote_path: str, remote_root: str) -> None:
        sftp = self._require_sftp()
        root = PurePosixPath(remote_root)
        parent = PurePosixPath(remote_path).parent
        current = root
        relative_parts = parent.relative_to(root).parts
        for part in relative_parts:
            current /= part
            try:
                attributes = sftp.lstat(str(current))
            except OSError:
                sftp.mkdir(str(current))
                continue
            if stat.S_ISLNK(attributes.st_mode) or not stat.S_ISDIR(attributes.st_mode):
                raise ValueError(f"unsafe remote parent: {current}")

    def _remote_sha256(self, remote_path: str) -> str:
        import hashlib

        sftp = self._require_sftp()
        digest = hashlib.sha256()
        with sftp.file(remote_path, "rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def upload(self, manifest: DeploymentManifest, project_root: Path) -> dict[str, Any]:
        """Upload only automatic entries after marker, hash, and conflict checks."""
        verify_local_manifest(manifest, project_root)
        self.verify_project_marker(manifest.remote_root, manifest.project_id)
        sftp = self._require_sftp()
        uploaded: list[dict[str, Any]] = []
        verified_existing: list[dict[str, Any]] = []
        for entry in manifest.entries:
            if entry.mode in {TransferMode.MANUAL, TransferMode.REMOTE_EXISTING}:
                remote_path = self._remote_path(manifest.remote_root, entry.remote_path)
                attributes = sftp.lstat(remote_path)
                if (
                    stat.S_ISLNK(attributes.st_mode)
                    or not stat.S_ISREG(attributes.st_mode)
                    or attributes.st_size != entry.size_bytes
                    or self._remote_sha256(remote_path) != entry.sha256
                ):
                    raise ValueError(f"remote existing file mismatch: {entry.remote_path}")
                verified_existing.append({"path": entry.remote_path, "sha256": entry.sha256})
                continue
            if entry.mode is not TransferMode.AUTO:
                continue
            local_path = resolve_within(project_root, entry.source_path, must_exist=True)
            remote_path = self._remote_path(manifest.remote_root, entry.remote_path)
            try:
                remote_attributes = sftp.lstat(remote_path)
            except OSError:
                remote_attributes = None
            if remote_attributes is not None:
                if stat.S_ISLNK(remote_attributes.st_mode) or not stat.S_ISREG(
                    remote_attributes.st_mode
                ):
                    raise ValueError(f"remote target is not a regular file: {entry.remote_path}")
                remote_digest = self._remote_sha256(remote_path)
                if entry.remote_path.endswith(".md"):
                    if entry.expected_remote_sha256 is None:
                        raise ValueError(
                            f"existing remote Markdown requires previous hash: {entry.remote_path}"
                        )
                    if remote_digest != entry.expected_remote_sha256:
                        raise ValueError(f"remote Markdown conflict: {entry.remote_path}")
                elif entry.expected_remote_sha256 and remote_digest != entry.expected_remote_sha256:
                    raise ValueError(f"remote file conflict: {entry.remote_path}")

            self._ensure_remote_parent(remote_path, manifest.remote_root)
            temporary = f"{remote_path}.part-{uuid4().hex}"
            sftp.put(str(local_path), temporary)
            if self._remote_sha256(temporary) != entry.sha256:
                sftp.remove(temporary)
                raise ValueError(f"remote upload hash mismatch: {entry.remote_path}")
            self._replace_remote_file(temporary, remote_path)
            uploaded.append({"path": entry.remote_path, "sha256": entry.sha256})

        return {
            "schema_version": 1,
            "deployment_id": manifest.deployment_id,
            "project_id": manifest.project_id,
            "uploaded": uploaded,
            "verified_existing": verified_existing,
        }

    def download(
        self,
        *,
        remote_root: str,
        project_id: str,
        local_root: Path,
        file_specs: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Download an explicit result list while excluding models, caches, and secrets."""
        self.verify_project_marker(remote_root, project_id)
        sftp = self._require_sftp()
        completed: list[dict[str, Any]] = []
        for spec in file_specs:
            remote_relative, local_relative = validate_download_paths(
                str(spec["remote_path"]), str(spec["local_path"])
            )

            expected_size = int(spec["size_bytes"])
            expected_sha = str(spec["sha256"])
            remote_path = str(PurePosixPath(remote_root).joinpath(remote_relative))
            attributes = sftp.lstat(remote_path)
            if not stat.S_ISREG(attributes.st_mode) or attributes.st_size != expected_size:
                raise ValueError(f"remote result size/type mismatch: {remote_relative}")
            local_path = resolve_within(local_root, local_relative.as_posix())
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if shutil.disk_usage(local_path.parent).free < expected_size * 2:
                raise ValueError(f"insufficient local disk for: {local_relative}")
            temporary = local_path.with_name(f"{local_path.name}.part-{uuid4().hex}")
            sftp.get(remote_path, str(temporary))
            if sha256_file(temporary) != expected_sha:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"download hash mismatch: {remote_relative}")
            temporary.replace(local_path)
            completed.append({"path": local_relative.as_posix(), "sha256": expected_sha})
        return completed
