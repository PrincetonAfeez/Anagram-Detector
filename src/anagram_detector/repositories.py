from __future__ import annotations

from abc import ABC, abstractmethod
from importlib import resources
from pathlib import Path
from typing import Iterator

from anagram_detector.cache import file_content_hash, stable_hash
from anagram_detector.errors import UnsupportedLanguageError
from anagram_detector.models import Word
from anagram_detector.normalization import NormalizationPipeline
from anagram_detector.signatures import SignatureStrategy


class DictionaryRepository(ABC):
    def __init__(
        self,
        pipeline: NormalizationPipeline,
        strategy: SignatureStrategy,
    ) -> None:
        self.pipeline = pipeline
        self.strategy = strategy

    @abstractmethod
    def raw_words(self) -> Iterator[str]:
        """Yield raw words from the backing store."""

    @abstractmethod
    def cache_identity(self) -> str:
        """Return a content-aware identity for cache invalidation."""

    def load(self) -> Iterator[Word]:
        for raw in self.raw_words():
            original = raw.strip()
            if not original:
                continue
            normalized = self.pipeline.normalize(original)
            if not normalized:
                continue
            yield Word(original, normalized, self.strategy.signature(normalized))


class FileDictionaryRepository(DictionaryRepository):
    def __init__(
        self,
        path: Path,
        pipeline: NormalizationPipeline,
        strategy: SignatureStrategy,
    ) -> None:
        super().__init__(pipeline, strategy)
        self.path = path.expanduser().resolve()

    def raw_words(self) -> Iterator[str]:
        with self.path.open("r", encoding="utf-8") as file:
            yield from file

    def cache_identity(self) -> str:
        return f"file:{self.path}:{file_content_hash(self.path)}"

class BundledDictionaryRepository(FileDictionaryRepository):
    def __init__(
        self,
        language: str,
        pipeline: NormalizationPipeline,
        strategy: SignatureStrategy,
    ) -> None:
        data_root = resources.files("anagram_detector").joinpath("data")
        dictionary = data_root.joinpath(f"{language}.txt")
        if not dictionary.is_file():
            raise UnsupportedLanguageError(f"No bundled dictionary exists for language '{language}'.")
        super().__init__(Path(str(dictionary)), pipeline, strategy)
        self.language = language

    def cache_identity(self) -> str:
        return f"bundled:{self.language}:{file_content_hash(self.path)}"

