"""Test properties."""

from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st  # noqa: E402

from anagram_detector.engine import AnagramDetector  # noqa: E402
from anagram_detector.normalization import default_pipeline  # noqa: E402
from anagram_detector.repositories import InMemoryDictionaryRepository  # noqa: E402
from anagram_detector.signatures import CounterSignature, SortedSignature  # noqa: E402


LETTERS = st.text(alphabet=list("abcdefghijklmnopqrstuvwxyz"), min_size=1, max_size=10)
NO_DATABASE = settings(database=None)


def property_detector() -> AnagramDetector:
    pipeline = default_pipeline()
    strategy = SortedSignature()
    repository = InMemoryDictionaryRepository([], pipeline, strategy)
    return AnagramDetector(repository, pipeline, strategy)


@given(base=LETTERS, data=st.data())
@NO_DATABASE
def test_any_permutation_is_an_anagram(base: str, data: st.DataObject) -> None:
    permutation = "".join(data.draw(st.permutations(tuple(base))))

    assert property_detector().check(base, permutation).is_match is True


@given(first=LETTERS, second=LETTERS)
@NO_DATABASE
def test_anagram_check_is_symmetric(first: str, second: str) -> None:
    subject = property_detector()

    assert subject.check(first, second).is_match == subject.check(second, first).is_match


@given(base=LETTERS, data=st.data())
@NO_DATABASE
def test_anagram_check_is_transitive(base: str, data: st.DataObject) -> None:
    first = "".join(data.draw(st.permutations(tuple(base))))
    second = "".join(data.draw(st.permutations(tuple(base))))
    subject = property_detector()

    assert subject.check(base, first).is_match is True
    assert subject.check(first, second).is_match is True
    assert subject.check(base, second).is_match is True


@given(first=LETTERS, second=LETTERS)
@NO_DATABASE
def test_sorted_and_counter_strategies_agree(first: str, second: str) -> None:
    sorted_strategy = SortedSignature()
    counter_strategy = CounterSignature()

    assert (sorted_strategy.signature(first) == sorted_strategy.signature(second)) == (
        counter_strategy.signature(first) == counter_strategy.signature(second)
    )
