"""Portable prompt template models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptTemplate:
    """A provider-neutral text template with declared variables."""

    # TODO: Add schema versioning after template persistence is introduced.

    name: str
    content: str
    variables: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, str] = field(default_factory=dict)
