"""Test the engine."""

from pathlib import Path

from anagram_detector.engine import AnagramDetector
from anagram_detector.normalization import default_pipeline
from anagram_detector.repositories import InMemoryDictionaryRepository
from anagram_detector.signatures import SortedSignature


def detector(tmp_path: Path) -> AnagramDetector:
    pipeline = default_pipeline()
    strategy = SortedSignature()
    repository = InMemoryDictionaryRepository(
        ["listen", "silent", "enlist", "tea", "eat", "ate", "tan", "ant", "stand"],
        pipeline,
        strategy,
    )
    return AnagramDetector(repository, pipeline, strategy, cache_dir=tmp_path)


def test_check_is_symmetric(tmp_path: Path) -> None:
    subject = detector(tmp_path)

    assert subject.check("listen", "silent").is_match is True
    assert subject.check("silent", "listen").is_match is True


def test_find_exact_uses_index(tmp_path: Path) -> None:
    subject = detector(tmp_path)

    matches = {word.original for word in subject.find_exact("listen").matches}

    assert matches == {"listen", "silent", "enlist"}


def test_find_subanagrams(tmp_path: Path) -> None:
    subject = detector(tmp_path)

    matches = {word.original for word in subject.find_subanagrams("stand").matches}

    assert {"tan", "ant", "stand"}.issubset(matches)


def test_multi_word_detection(tmp_path: Path) -> None:
    subject = detector(tmp_path)

    matches = {
        tuple(word.original for word in match)
        for match in subject.find_multi_word("teatan", max_words=3).multi_word_matches
    }

    assert ("tea", "tan") in matches or ("tan", "tea") in matches


def test_group_words(tmp_path: Path) -> None:
    subject = detector(tmp_path)

    groups = subject.group_words(["care", "race", "acre", "hello"]).groups

    assert len(groups) == 1
    assert {word.original for word in groups[0].words} == {"care", "race", "acre"}
