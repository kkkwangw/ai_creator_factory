"""Contracts for discovering and managing external capability plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class PluginKind(StrEnum):
    """Supported extension families."""

    LLM = "llm"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    STORAGE = "storage"


class PluginState(StrEnum):
    """Lifecycle state visible to the runtime."""

    REGISTERED = "registered"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


class ApprovalStatus(StrEnum):
    """Whether a plugin/model combination may enter unattended production."""

    PLANNED = "planned"
    CANDIDATE = "candidate"
    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PluginMetadata:
    """Identity and compatibility information supplied by a plugin."""

    name: str
    kind: PluginKind
    version: str
    api_version: str = "1"
    capabilities: Sequence[str] = field(default_factory=tuple)
    approval_status: ApprovalStatus = ApprovalStatus.PLANNED


class Plugin(ABC):
    """Provider adapter lifecycle contract."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return immutable plugin metadata."""

    @abstractmethod
    def configure(self, config: Mapping[str, Any]) -> None:
        """Validate and retain plugin-specific configuration."""

    @abstractmethod
    def start(self) -> None:
        """Acquire resources required by this plugin."""

    @abstractmethod
    def stop(self) -> None:
        """Release resources held by this plugin."""


class PluginManager(ABC):
    """Discovery, registration, lookup, and lifecycle boundary for plugins."""

    @abstractmethod
    def discover(self, paths: Iterable[Path]) -> Sequence[Plugin]:
        """Discover plugin candidates without starting them.

        TODO: Define the manifest format and trusted loading policy.
        """

    @abstractmethod
    def register(self, plugin: Plugin) -> None:
        """Register a validated plugin instance."""

    @abstractmethod
    def get(self, name: str) -> Plugin:
        """Return a registered plugin by stable name."""

    @abstractmethod
    def start(self, name: str) -> None:
        """Start one registered plugin."""

    @abstractmethod
    def stop(self, name: str) -> None:
        """Stop one registered plugin."""

    @abstractmethod
    def states(self) -> Mapping[str, PluginState]:
        """Return a read-only lifecycle snapshot."""
