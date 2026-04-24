"""Composable normalization pipeline."""

from __future__ import annotations

import string
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


class Normalizer(Protocol):
    """Single normalization strategy."""

    @property
    def name(self) -> str:
        """Human-readable strategy name."""

    def normalize(self, text: str) -> str:
        """Return normalized text."""


@dataclass(frozen=True, slots=True)
class CaseFolder:
    """Case-fold text."""
    name: str = "casefold"

    def normalize(self, text: str) -> str:
        return text.casefold()


@dataclass(frozen=True, slots=True)
class WhitespaceStripper:
    """Strip whitespace."""
    name: str = "whitespace"

    def normalize(self, text: str) -> str:
        return "".join(char for char in text if not char.isspace())


@dataclass(frozen=True, slots=True)
class PunctuationStripper:
    """Strip punctuation."""
    name: str = "punctuation"

    def normalize(self, text: str) -> str:
        return text.translate(_ASCII_PUNCTUATION_TABLE)


@dataclass(frozen=True, slots=True)
class DiacriticFolder:
    """Strip diacritics."""
    name: str = "diacritics"

    def normalize(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(char for char in decomposed if not unicodedata.combining(char))


@dataclass(frozen=True, slots=True)
class NonAlphaStripper:
    """Strip non-alpha characters."""
    name: str = "nonalpha"

    def normalize(self, text: str) -> str:
        return "".join(char for char in text if char.isalpha())


_ASCII_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


@dataclass(frozen=True, slots=True)
class NormalizationPipeline:
    """An ordered chain of normalization strategies."""

    normalizers: tuple[Normalizer, ...]

    def normalize(self, text: str) -> str:
        """Normalize text using the pipeline."""
        return _normalize_cached(self.cache_key, text, self.normalizers)

    @property
    def cache_key(self) -> str:
        """Get the cache key for the pipeline."""
        return "+".join(normalizer.name for normalizer in self.normalizers)


@lru_cache(maxsize=8192)
def _normalize_cached(
    _cache_key: str,
    text: str,
    normalizers: tuple[Normalizer, ...],
) -> str:
    """Normalize text using the pipeline."""
    current = text
    for normalizer in normalizers:
        current = normalizer.normalize(current)
    return current


def default_pipeline(*, fold_diacritics: bool = True) -> NormalizationPipeline:
    """Build the default normalization chain."""

    normalizers: list[Normalizer] = [
        CaseFolder(),
        WhitespaceStripper(),
        PunctuationStripper(),
    ]
    if fold_diacritics:
        normalizers.append(DiacriticFolder())
    normalizers.append(NonAlphaStripper())
    return NormalizationPipeline(tuple(normalizers))


def pipeline_from_names(names: list[str] | tuple[str, ...]) -> NormalizationPipeline:
    """Build a pipeline from config names."""

    registry: dict[str, Normalizer] = {
        "casefold": CaseFolder(),
        "whitespace": WhitespaceStripper(),
        "punctuation": PunctuationStripper(),
        "diacritics": DiacriticFolder(),
        "nonalpha": NonAlphaStripper(),
    }
    unknown = [name for name in names if name not in registry]
    if unknown:
        available = ", ".join(sorted(registry))
        bad = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown normalizer(s): {bad}. Choose from: {available}.")
    return NormalizationPipeline(tuple(registry[name] for name in names))
