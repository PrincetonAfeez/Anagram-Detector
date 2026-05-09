"""Domain models used by the detector."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum


class MatchType(Enum):
    """Supported matching modes."""

    EXACT = "exact"
    SUBSET = "subset"
    SUPERSET = "superset"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class Word:
    """A dictionary word plus its normalized and canonical representations."""

    original: str
    normalized: str
    signature: Hashable

    def __str__(self) -> str:
        return self.original


@dataclass(frozen=True, slots=True)
class AnagramGroup:
    """Words sharing the same anagram signature."""

    signature: Hashable
    words: frozenset[Word]


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Rich result object returned by detector queries."""

    query: str
    match_type: MatchType
    matches: tuple[Word, ...] = field(default_factory=tuple)
    total_candidates_searched: int = 0
    elapsed_ms: float = 0.0
    compared_to: str | None = None
    is_match: bool | None = None
    groups: tuple[AnagramGroup, ...] = field(default_factory=tuple)
    multi_word_matches: tuple[tuple[Word, ...], ...] = field(default_factory=tuple)
