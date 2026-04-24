"""Core anagram detection engine."""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from pathlib import Path

from anagram_detector.cache import default_cache_dir, disk_cached, stable_hash
from anagram_detector.errors import InvalidInputError
from anagram_detector.models import AnagramGroup, MatchResult, MatchType, Word
from anagram_detector.normalization import NormalizationPipeline
from anagram_detector.repositories import DictionaryRepository
from anagram_detector.signatures import SignatureStrategy


@dataclass(frozen=True, slots=True)
class AnagramIndex:
    """Signature -> words index built once per dictionary."""

    groups: dict[Hashable, frozenset[Word]]
    words: tuple[Word, ...]

    @classmethod
    def build(cls, words: Iterable[Word]) -> AnagramIndex:
        """Build the anagram index."""
        grouped: dict[Hashable, set[Word]] = defaultdict(set)
        unique_words = tuple(dict.fromkeys(words))
        for word in unique_words:
            grouped[word.signature].add(word)
        return cls(
            groups={signature: frozenset(group) for signature, group in grouped.items()},
            words=unique_words,
        )

    def exact(self, signature: Hashable) -> tuple[Word, ...]:
        """Find exact anagrams."""
        return tuple(sorted(self.groups.get(signature, ()), key=_word_sort_key))

    def subanagrams(self, normalized: str, min_length: int = 1) -> tuple[Word, ...]:
        """Find subanagrams."""
        available = Counter(normalized)
        matches: list[Word] = []
        max_length = len(normalized)
        for word in self.words:
            length = len(word.normalized)
            if length < min_length or length > max_length:
                continue
            if _counter_contains(available, Counter(word.normalized)):
                matches.append(word)
        return tuple(sorted(matches, key=lambda word: (len(word.normalized), word.original.casefold())))

    def multi_word(
        self,
        normalized: str,
        *,
        max_words: int = 3,
        min_length: int = 1,
        max_results: int = 100,
    ) -> tuple[tuple[Word, ...], ...]:
        """Find multi-word anagrams."""
        target = Counter(normalized)
        candidates = [
            word
            for word in self.words
            if min_length <= len(word.normalized) <= len(normalized)
            and _counter_contains(target, Counter(word.normalized))
        ]
        candidates.sort(key=lambda word: (len(word.normalized), word.normalized, word.original.casefold()))
        candidate_counters = [Counter(word.normalized) for word in candidates]
        results: list[tuple[Word, ...]] = []
        seen: set[tuple[str, ...]] = set()
        dead_states: set[tuple[tuple[tuple[str, int], ...], int, int]] = set()

        def search(
            remaining: Counter[str],
            start_index: int,
            path: list[Word],
        ) -> bool:
            """Search for multi-word anagrams."""
            if len(results) >= max_results:
                return True
            if not remaining:
                if len(path) >= 2:
                    key = tuple(sorted(word.original.casefold() for word in path))
                    if key not in seen:
                        seen.add(key)
                        results.append(tuple(path))
                        return True
                return False
            if len(path) >= max_words:
                return False

            state = (tuple(sorted(remaining.items())), start_index, max_words - len(path))
            if state in dead_states:
                return False

            found = False

            for index in range(start_index, len(candidates)):
                word = candidates[index]
                word_counter = candidate_counters[index]
                if not _counter_contains(remaining, word_counter):
                    continue
                next_remaining = remaining - word_counter
                path.append(word)
                if search(+next_remaining, index, path):
                    found = True
                path.pop()
                if len(results) >= max_results:
                    return True

            if not found:
                dead_states.add(state)
            return found

        search(target, 0, [])
        return tuple(results)


class AnagramDetector:
    """High-level query API over a lazily loaded index."""

    def __init__(
        self,
        repository: DictionaryRepository,
        pipeline: NormalizationPipeline,
        strategy: SignatureStrategy,
        *,
        cache_dir: Path | None = None,
        min_length: int = 1,
    ) -> None:
        """Initialize the anagram detector."""
        self.repository = repository
        self.pipeline = pipeline
        self.strategy = strategy
        self.cache_dir = cache_dir or default_cache_dir()
        self.min_length = min_length
        self._index: AnagramIndex | None = None

    @property
    def index(self) -> AnagramIndex:
        if self._index is None:
            """Load the index from cache."""
            self._index = _load_index(
                self.repository,
                self.repository.cache_identity(),
                self.pipeline.cache_key,
                self.strategy.name,
                self.cache_dir,
            )
        return self._index

    def check(self, first: str, second: str) -> MatchResult:
        """Check if two words are anagrams."""
        started = time.perf_counter()
        first_normalized = self._normalize_or_raise(first)
        second_normalized = self._normalize_or_raise(second)
        is_match = self.strategy.signature(first_normalized) == self.strategy.signature(second_normalized)
        return MatchResult(
            query=first,
            compared_to=second,
            match_type=MatchType.EXACT,
            is_match=is_match,
            total_candidates_searched=1,
            elapsed_ms=_elapsed_ms(started),
        )

    def find_exact(self, query: str) -> MatchResult:
        """Find exact anagrams."""
        started = time.perf_counter()
        normalized = self._normalize_or_raise(query)
        signature = self.strategy.signature(normalized)
        matches = tuple(
            word for word in self.index.exact(signature) if len(word.normalized) >= self.min_length
        )
        return MatchResult(
            query=query,
            match_type=MatchType.EXACT,
            matches=matches,
            total_candidates_searched=1,
            elapsed_ms=_elapsed_ms(started),
        )

    def find_subanagrams(self, query: str) -> MatchResult:
        """Find subanagrams."""
        started = time.perf_counter()
        normalized = self._normalize_or_raise(query)
        matches = self.index.subanagrams(normalized, self.min_length)
        return MatchResult(
            query=query,
            match_type=MatchType.SUBSET,
            matches=matches,
            total_candidates_searched=len(self.index.words),
            elapsed_ms=_elapsed_ms(started),
        )

    def find_multi_word(
        self,
        query: str,
        *,
        max_words: int = 3,
        max_results: int = 100,
    ) -> MatchResult:
        """Find multi-word anagrams."""
        started = time.perf_counter()
        normalized = self._normalize_or_raise(query)
        matches = self.index.multi_word(
            normalized,
            max_words=max_words,
            min_length=self.min_length,
            max_results=max_results,
        )
        return MatchResult(
            query=query,
            match_type=MatchType.PARTIAL,
            multi_word_matches=matches,
            total_candidates_searched=len(self.index.words),
            elapsed_ms=_elapsed_ms(started),
        )

    def group_words(self, words: Iterable[str]) -> MatchResult:
        """Group words into anagram groups."""
        started = time.perf_counter()
        grouped: dict[Hashable, set[Word]] = defaultdict(set)
        count = 0
        for raw in words:
            original = raw.strip()
            if not original:
                continue
            normalized = self.pipeline.normalize(original)
            if len(normalized) < self.min_length:
                continue
            word = Word(original, normalized, self.strategy.signature(normalized))
            grouped[word.signature].add(word)
            count += 1

        groups = tuple(
            sorted(
                (
                    AnagramGroup(signature, frozenset(group))
                    for signature, group in grouped.items()
                    if len(group) >= 2
                ),
                key=lambda group: (-len(group.words), str(group.signature)),
            )
        )
        return MatchResult(
            query="group",
            match_type=MatchType.EXACT,
            groups=groups,
            total_candidates_searched=count,
            elapsed_ms=_elapsed_ms(started),
        )

    def _normalize_or_raise(self, text: str) -> str:
        """Normalize the text or raise an error if it contains no alphabetic characters after normalization."""
        normalized = self.pipeline.normalize(text)
        if not normalized:
            raise InvalidInputError("Input must contain at least one alphabetic character after normalization.")
        return normalized


def _index_cache_path(
    repository: DictionaryRepository,
    repository_identity: str,
    pipeline_key: str,
    strategy_name: str,
    cache_dir: Path,
) -> Path:
    """Generate the cache path for the index."""
    del repository
    key = stable_hash(f"{repository_identity}|{pipeline_key}|{strategy_name}")
    return cache_dir / f"index-{key}.pickle"


@disk_cached(_index_cache_path)
def _load_index(
    repository: DictionaryRepository,
    repository_identity: str,
    pipeline_key: str,
    strategy_name: str,
    cache_dir: Path,
) -> AnagramIndex:

    del repository_identity, pipeline_key, strategy_name, cache_dir
    return AnagramIndex.build(repository.load())


def _counter_contains(available: Counter[str], needed: Counter[str]) -> bool:
    """Check if all characters in the needed counter are available in the available counter."""
    return all(available[char] >= count for char, count in needed.items())


def _elapsed_ms(started: float) -> float:
    """Calculate elapsed time in milliseconds."""
    return (time.perf_counter() - started) * 1000


def _word_sort_key(word: Word) -> tuple[str, str]:
    """Sort words by normalized form and original string case-folded."""
    return (word.normalized, word.original.casefold())
