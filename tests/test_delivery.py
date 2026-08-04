"""Tests for evidence-derived final media specifications."""

import json
from pathlib import Path

import pytest

from media.delivery import (
    DeliveryValidationError,
    validate_cover_probe,
    validate_video_probe,
    verify_delivery,
)


def valid_video_probe() -> dict[str, object]:
    return {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "24/1",
                "r_frame_rate": "24/1",
            },
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "52.0"},
    }


def test_valid_video_probe_passes() -> None:
    evidence = validate_video_probe(valid_video_probe())

    assert evidence["fps"] == 24
    assert evidence["duration"] == 52.0


def test_wrong_duration_fails_even_if_status_might_say_done() -> None:
    payload = valid_video_probe()
    payload["format"] = {"duration": "61.0"}

    with pytest.raises(DeliveryValidationError, match="duration"):
        validate_video_probe(payload)


def test_variable_frame_rate_is_rejected() -> None:
    payload = valid_video_probe()
    payload["streams"][0]["r_frame_rate"] = "30/1"

    with pytest.raises(DeliveryValidationError, match="constant 24fps"):
        validate_video_probe(payload)


def test_cover_requires_exact_dimensions() -> None:
    with pytest.raises(DeliveryValidationError, match="1080x1920"):
        validate_cover_probe(
            {"streams": [{"codec_type": "video", "width": 1080, "height": 1080}]}
        )


def test_delivery_manifest_must_match_current_project(tmp_path: Path) -> None:
    (tmp_path / "PROJECT.md").write_text(
        '+++\nproject_id = "project-one"\n+++\n', encoding="utf-8"
    )
    manifest_path = tmp_path / "runs" / "run-one" / "evidence" / "delivery.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_id": "project-two",
                "run_id": "run-one",
                "files": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(DeliveryValidationError, match="PROJECT.md"):
        verify_delivery(project_root=tmp_path, manifest_path=manifest_path)


def test_delivery_manifest_path_must_match_run_id(tmp_path: Path) -> None:
    (tmp_path / "PROJECT.md").write_text(
        '+++\nproject_id = "project-one"\n+++\n', encoding="utf-8"
    )
    manifest_path = tmp_path / "runs" / "run-other" / "evidence" / "delivery.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_id": "project-one",
                "run_id": "run-one",
                "files": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(DeliveryValidationError, match="runs/<run_id>/evidence"):
        verify_delivery(project_root=tmp_path, manifest_path=manifest_path)
