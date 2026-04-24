from __future__ import annotations

from collections import Counter
from collections.abc import Hashable
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


class SignatureStrategy(Protocol):
    @property
    def name(self) -> str:
        """Human-readable strategy name."""

    def signature(self, normalized: str) -> Hashable:
        """Return a hashable value shared by anagrams."""

