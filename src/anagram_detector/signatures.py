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

@dataclass(frozen=True, slots=True)
class SortedSignature:
    name: str = "sorted"

    def signature(self, normalized: str) -> str:
        return _sorted_signature(normalized)

@dataclass(frozen=True, slots=True)
class CounterSignature:
    name: str = "counter"

    def signature(self, normalized: str) -> frozenset[tuple[str, int]]:
        return _counter_signature(normalized)

