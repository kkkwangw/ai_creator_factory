"""Top-level runtime orchestration contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.config import Settings
from core.event_bus import EventBus
from core.plugin_manager import PluginManager


@dataclass(frozen=True)
class RuntimeDependencies:
    """Explicit dependencies owned by the application runtime."""

    settings: Settings
    plugin_manager: PluginManager
    event_bus: EventBus


class Runtime(ABC):
    """Coordinates startup and shutdown without provider knowledge."""

    @abstractmethod
    def start(self) -> None:
        """Validate configuration and start enabled components."""

    @abstractmethod
    def stop(self) -> None:
        """Stop components and release runtime resources."""

    @abstractmethod
    def run(self) -> None:
        """Run the configured workload.

        TODO: Define cancellation and failure semantics with the workflow engine.
        """

