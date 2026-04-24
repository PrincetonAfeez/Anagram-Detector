"""Test signatures."""

from anagram_detector.signatures import CounterSignature, PrimeSignature, SortedSignature


def test_signature_strategies_agree_for_ascii_anagrams() -> None:
    first = "listen"
    second = "silent"

    for strategy in (SortedSignature(), CounterSignature(), PrimeSignature()):
        assert strategy.signature(first) == strategy.signature(second)


def test_signature_strategies_reject_non_anagrams() -> None:
    first = "listen"
    second = "stone"

    for strategy in (SortedSignature(), CounterSignature(), PrimeSignature()):
        assert strategy.signature(first) != strategy.signature(second)


def test_prime_strategy_falls_back_for_non_ascii() -> None:
    strategy = PrimeSignature()

    assert strategy.signature("café") == strategy.signature("facé")
