"""Anagram signature strategies."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


class SignatureStrategy(Protocol):
    """Strategy for creating an anagram-equivalence signature."""

    @property
    def name(self) -> str:
        """Human-readable strategy name."""

    def signature(self, normalized: str) -> Hashable:
        """Return a hashable value shared by anagrams."""


@dataclass(frozen=True, slots=True)
class SortedSignature:
    """Readable baseline: O(n log n)."""

    name: str = "sorted"

    def signature(self, normalized: str) -> str:
        """Compute the sorted signature."""
        return _sorted_signature(normalized)


@dataclass(frozen=True, slots=True)
class CounterSignature:
    """Linear-time signature that preserves useful letter counts."""

    name: str = "counter"

    def signature(self, normalized: str) -> frozenset[tuple[str, int]]:
        return _counter_signature(normalized)


@dataclass(frozen=True, slots=True)
class PrimeSignature:
    """Prime-product trick for a-z words.

    This is elegant and fast for short ASCII words, but the product becomes very large for
    long inputs. For non-ASCII letters, it falls back to a sorted signature to avoid collisions.
    """

    name: str = "prime"

    def signature(self, normalized: str) -> Hashable:
        """Compute the prime product signature."""
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
    """Compute the sorted signature."""
    return "".join(sorted(normalized))


@lru_cache(maxsize=32768)
def _counter_signature(normalized: str) -> frozenset[tuple[str, int]]:
    """Compute the counter signature."""
    return frozenset(Counter(normalized).items())


@lru_cache(maxsize=32768)
def _prime_signature(normalized: str) -> Hashable:
    """Compute the prime product signature."""
    product = 1
    for char in normalized:
        prime = _PRIMES.get(char)
        if prime is None:
            return ("prime-fallback", _sorted_signature(normalized))
        product *= prime
    return product


def strategy_from_name(name: str) -> SignatureStrategy:
    """Resolve a strategy by CLI/config name."""

    strategies: dict[str, SignatureStrategy] = {
        "sorted": SortedSignature(),
        "counter": CounterSignature(),
        "prime": PrimeSignature(),
    }
    try:
        return strategies[name]
    except KeyError as exc:
        names = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown strategy '{name}'. Choose one of: {names}.") from exc


def available_strategy_names() -> tuple[str, ...]:
    """Get the names of all available signature strategies."""
    return ("sorted", "counter", "prime")
