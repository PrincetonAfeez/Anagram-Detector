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

