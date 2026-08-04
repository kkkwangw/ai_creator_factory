"""Prompt construction boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from prompt.templates import PromptTemplate


class PromptBuilder(ABC):
    """Renders validated templates without provider-specific syntax."""

    @abstractmethod
    def build(self, template: PromptTemplate, values: Mapping[str, Any]) -> str:
        """Render one template.

        TODO: Define escaping and structured multimodal prompt semantics.
        """

