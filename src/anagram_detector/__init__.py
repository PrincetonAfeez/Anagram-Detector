"""Anagram Detector package."""

from anagram_detector.engine import AnagramDetector, AnagramIndex
from anagram_detector.errors import (
    AnagramError,
    DictionaryNotLoadedError,
    InvalidInputError,
    UnsupportedLanguageError,
)
from anagram_detector.models import AnagramGroup, MatchResult, MatchType, Word

__all__ = [
    "AnagramDetector",
    "AnagramError",
    "AnagramGroup",
    "AnagramIndex",
    "DictionaryNotLoadedError",
    "InvalidInputError",
    "MatchResult",
    "MatchType",
    "UnsupportedLanguageError",
    "Word",
]
