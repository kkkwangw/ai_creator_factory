"""Verify delivery artifacts from real files, hashes, and ffprobe output."""

from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from utils.frontmatter import FrontmatterError, parse_toml_frontmatter
from utils.hashing import sha256_file
from utils.paths import resolve_within
from workflow.task import validate_identifier

REQUIRED_ROLES = {"final_video", "cover", "release_markdown", "release_json"}


class DeliveryValidationError(ValueError):
    """Raised when delivery artifacts fail their current technical contract."""


def run_ffprobe(path: Path, ffprobe: str = "ffprobe") -> dict[str, Any]:
    """Return machine-readable media metadata without invoking a shell."""
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise DeliveryValidationError(f"ffprobe failed for {path.name}: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise DeliveryValidationError(f"ffprobe returned invalid JSON for {path.name}") from error


def _duration(payload: dict[str, Any]) -> float:
    try:
        return float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError) as error:
        raise DeliveryValidationError("ffprobe result has no valid duration") from error


def validate_video_probe(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the fixed book-list-v1 final video contract."""
    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if video is None or audio is None:
        raise DeliveryValidationError("final video must contain video and audio streams")
    if (video.get("width"), video.get("height")) != (1080, 1920):
        raise DeliveryValidationError("final video must be 1080x1920")
    if video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p":
        raise DeliveryValidationError("final video must be H.264 yuv420p")
    try:
        average_frame_rate = Fraction(video["avg_frame_rate"])
        real_frame_rate = Fraction(video["r_frame_rate"])
    except (KeyError, ValueError, ZeroDivisionError) as error:
        raise DeliveryValidationError("final video has no valid frame rate") from error
    if average_frame_rate != 24 or real_frame_rate != 24:
        raise DeliveryValidationError("final video must use constant 24fps")
    if audio.get("codec_name") != "aac":
        raise DeliveryValidationError("final video audio must use AAC")
    duration = _duration(payload)
    if not 45 <= duration <= 60:
        raise DeliveryValidationError("final video duration must be between 45 and 60 seconds")
    return {"width": 1080, "height": 1920, "fps": 24, "duration": duration}


def validate_cover_probe(payload: dict[str, Any]) -> dict[str, int]:
    """Validate the fixed publish-cover dimensions."""
    streams = payload.get("streams", [])
    image = next((item for item in streams if item.get("codec_type") == "video"), None)
    if image is None or (image.get("width"), image.get("height")) != (1080, 1920):
        raise DeliveryValidationError("cover must be a decodable 1080x1920 image")
    return {"width": 1080, "height": 1920}


def verify_delivery(
    *, project_root: Path, manifest_path: Path, ffprobe: str = "ffprobe"
) -> dict[str, Any]:
    """Verify final delivery files without claiming that earlier Gates passed."""
    project_root = project_root.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if not manifest_path.is_relative_to(project_root):
        raise DeliveryValidationError("delivery manifest must remain inside the project")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version") != 1:
        raise DeliveryValidationError("unsupported delivery manifest schema_version")
    try:
        project_id = validate_identifier(str(manifest["project_id"]), field_name="project_id")
        run_id = validate_identifier(str(manifest["run_id"]), field_name="run_id")
    except (KeyError, ValueError) as error:
        raise DeliveryValidationError(
            "delivery manifest has invalid project/run identity"
        ) from error
    try:
        project, _ = parse_toml_frontmatter(project_root / "PROJECT.md", max_bytes=16384)
    except (OSError, FrontmatterError) as error:
        raise DeliveryValidationError("PROJECT.md identity cannot be verified") from error
    if project.get("project_id") != project_id:
        raise DeliveryValidationError("delivery project_id does not match PROJECT.md")
    manifest_relative = manifest_path.relative_to(project_root)
    if (
        len(manifest_relative.parts) < 4
        or manifest_relative.parts[0] != "runs"
        or manifest_relative.parts[1] != run_id
        or manifest_relative.parts[2] != "evidence"
    ):
        raise DeliveryValidationError(
            "delivery manifest must be stored under runs/<run_id>/evidence"
        )

    files = manifest.get("files", [])
    role_list = [item.get("role") for item in files]
    roles = set(role_list)
    if len(role_list) != len(roles):
        raise DeliveryValidationError("delivery manifest contains duplicate roles")
    missing_roles = REQUIRED_ROLES - roles
    if missing_roles:
        raise DeliveryValidationError(f"delivery manifest missing roles: {sorted(missing_roles)}")

    evidence: list[dict[str, Any]] = []
    by_role: dict[str, Path] = {}
    for item in files:
        role = str(item["role"])
        relative_path = str(item["path"])
        if not relative_path.startswith("deliverables/current/"):
            raise DeliveryValidationError("delivery files must be under deliverables/current")
        path = resolve_within(project_root, relative_path, must_exist=True)
        expected_size = int(item["size_bytes"])
        expected_sha = str(item["sha256"])
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        if actual_size != expected_size or actual_sha != expected_sha:
            raise DeliveryValidationError(f"delivery evidence mismatch for {role}")
        by_role[role] = path
        evidence.append(
            {
                "role": role,
                "path": str(item["path"]),
                "size_bytes": actual_size,
                "sha256": actual_sha,
            }
        )

    with by_role["release_json"].open(encoding="utf-8") as handle:
        release_copy = json.load(handle)
    for required in ("primary_title", "body", "hashtags", "book_title", "author"):
        if required not in release_copy:
            raise DeliveryValidationError(f"release JSON missing field: {required}")

    video_evidence = validate_video_probe(run_ffprobe(by_role["final_video"], ffprobe))
    cover_evidence = validate_cover_probe(run_ffprobe(by_role["cover"], ffprobe))
    return {
        "schema_version": 1,
        "derived_status": "delivery_artifacts_verified",
        "project_id": project_id,
        "run_id": run_id,
        "workflow_ready": False,
        "workflow_blocker": "Gate 1-6 evidence validators are not implemented",
        "files": evidence,
        "video": video_evidence,
        "cover": cover_evidence,
    }
