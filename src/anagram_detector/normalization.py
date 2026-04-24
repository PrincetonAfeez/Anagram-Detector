from __future__ import annotations

import string
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


class Normalizer(Protocol):
    @property
    def name(self) -> str:
        """Human-readable strategy name."""

    def normalize(self, text: str) -> str:
        """Return normalized text."""

@dataclass(frozen=True, slots=True)
class CaseFolder:
    name: str = "casefold"

    def normalize(self, text: str) -> str:
        return text.casefold()

