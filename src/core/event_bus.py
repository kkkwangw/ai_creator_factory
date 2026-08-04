"""Provider-neutral event publishing contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """Immutable message exchanged between runtime components."""

    topic: str
    payload: Mapping[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus(ABC):
    """Minimal publish/subscribe boundary."""

    # TODO: Define async delivery and handler failure semantics before implementation.

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event to current subscribers."""

    @abstractmethod
    def subscribe(self, topic: str, handler: EventHandler) -> Callable[[], None]:
        """Register a handler and return an unsubscribe callback."""
