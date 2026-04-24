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

@dataclass(frozen=True, slots=True)
class WhitespaceStripper:
    name: str = "whitespace"

    def normalize(self, text: str) -> str:
        return "".join(char for char in text if not char.isspace())

@dataclass(frozen=True, slots=True)
class PunctuationStripper:
    name: str = "punctuation"

    def normalize(self, text: str) -> str:
        return text.translate(_ASCII_PUNCTUATION_TABLE)

@dataclass(frozen=True, slots=True)
class DiacriticFolder:
    name: str = "diacritics"

    def normalize(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(char for char in decomposed if not unicodedata.combining(char))

@dataclass(frozen=True, slots=True)
class DiacriticFolder:
    name: str = "diacritics"

    def normalize(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(char for char in decomposed if not unicodedata.combining(char))

@dataclass(frozen=True, slots=True)
class NonAlphaStripper:
    name: str = "nonalpha"

    def normalize(self, text: str) -> str:
        return "".join(char for char in text if char.isalpha())


_ASCII_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


@dataclass(frozen=True, slots=True)
class NormalizationPipeline:
    normalizers: tuple[Normalizer, ...]

    def normalize(self, text: str) -> str:
        return _normalize_cached(self.cache_key, text, self.normalizers)

    @property
    def cache_key(self) -> str:
        return "+".join(normalizer.name for normalizer in self.normalizers)

@lru_cache(maxsize=8192)
def _normalize_cached(
    _cache_key: str,
    text: str,
    normalizers: tuple[Normalizer, ...],
) -> str:
    current = text
    for normalizer in normalizers:
        current = normalizer.normalize(current)
    return current

def default_pipeline(*, fold_diacritics: bool = True) -> NormalizationPipeline:
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
