"""Test the normalization pipeline."""

import pytest

from anagram_detector.normalization import default_pipeline
from anagram_detector.normalization import pipeline_from_names


def test_default_normalization_handles_case_spacing_punctuation_and_diacritics() -> None:
    pipeline = default_pipeline()

    assert pipeline.normalize("Dirty room!!") == "dirtyroom"
    assert pipeline.normalize("CAFÉ") == "cafe"
    assert pipeline.normalize("a b\tc\n1!") == "abc"


def test_can_disable_diacritic_folding() -> None:
    pipeline = default_pipeline(fold_diacritics=False)

    assert pipeline.normalize("año") == "año"


def test_pipeline_from_names_rejects_unknown_entries() -> None:
    with pytest.raises(ValueError, match="Unknown normalizer"):
        pipeline_from_names(("casefold", "typo-normalizer"))
