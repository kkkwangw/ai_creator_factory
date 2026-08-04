"""Provider-neutral runtime policy loading."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    """Non-secret paths and runtime flags required by local automation."""

    environment: str = "development"
    log_level: str = "INFO"
    project_root: Path = Path(".")
    runtime_policy_path: Path = Path("config/runtime-policy.json")
    plugin_dirs: tuple[Path, ...] = (Path("plugins"),)

    @property
    def data_dir(self) -> Path:
        """Return the conventional data directory for compatibility."""
        return self.project_root / "data"

    @property
    def output_dir(self) -> Path:
        """Return the conventional output directory for compatibility."""
        return self.project_root / "outputs"

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build settings without loading provider or SSH secrets."""
        values = os.environ if environ is None else environ
        root = Path(values.get("AI_CREATOR_PROJECT_ROOT", "."))
        plugin_dirs = tuple(
            Path(item.strip())
            for item in values.get("AI_CREATOR_PLUGIN_DIRS", "plugins").split(os.pathsep)
            if item.strip()
        )
        return cls(
            environment=values.get("AI_CREATOR_ENV", "development"),
            log_level=values.get("AI_CREATOR_LOG_LEVEL", "INFO"),
            project_root=root,
            runtime_policy_path=Path(
                values.get("AI_CREATOR_RUNTIME_POLICY", "config/runtime-policy.json")
            ),
            plugin_dirs=plugin_dirs or (Path("plugins"),),
        )

    def validate(self) -> None:
        """Validate the fixed Python and project-root requirements."""
        if sys.version_info[:2] != (3, 11):
            raise ValueError("AI Creator Factory automation requires Python 3.11.x")
        if not self.environment.strip():
            raise ValueError("environment must not be empty")

    def load_runtime_policy(self) -> Mapping[str, Any]:
        """Load the versioned, non-secret runtime policy JSON."""
        path = self.project_root / self.runtime_policy_path
        with path.open(encoding="utf-8") as handle:
            policy = json.load(handle)
        if policy.get("schema_version") != 1:
            raise ValueError("unsupported runtime policy schema_version")
        return policy
