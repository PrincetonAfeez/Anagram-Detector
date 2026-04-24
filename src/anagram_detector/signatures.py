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

@dataclass(frozen=True, slots=True)
class PrimeSignature:
    name: str = "prime"

    def signature(self, normalized: str) -> Hashable:
        return _prime_signature(normalized)

_PRIMES = {
    char: prime
    for char, prime in zip(
        "abcdefghijklmnopqrstuvwxyz",
        [
            2,
            3,
            5,
            7,
            11,
            13,
            17,
            19,
            23,
            29,
            31,
            37,
            41,
            43,
            47,
            53,
            59,
            61,
            67,
            71,
            73,
            79,
            83,
            89,
            97,
            101,
        ],
        strict=True,
    )
}


@lru_cache(maxsize=32768)
def _sorted_signature(normalized: str) -> str:
    return "".join(sorted(normalized))
