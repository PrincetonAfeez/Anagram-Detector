from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum


class MatchType(Enum):
    EXACT = "exact"
    SUBSET = "subset"
    SUPERSET = "superset"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class Word:
    original: str
    normalized: str
    signature: Hashable

    def __str__(self) -> str:
        return self.original
