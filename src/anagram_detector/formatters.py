from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any, Protocol

from anagram_detector.colors import Ansi, color_enabled, paint
from anagram_detector.models import AnagramGroup, MatchResult, Word

class OutputFormatter(Protocol):
    def format(self, result: MatchResult) -> str:
        """Return display text."""

@dataclass(frozen=True, slots=True)
class PlainFormatter:
    use_color: bool = True

    def format(self, result: MatchResult) -> str:
        if result.is_match is not None:
            value = "true" if result.is_match else "false"
            color = Ansi.GREEN if result.is_match else Ansi.DIM
            return paint(value, color, enabled=self.use_color)

        if result.groups:
            lines = []
            for group in result.groups:
                words = " ".join(word.original for word in _sorted_words(group.words))
                lines.append(f"{paint(str(group.signature), Ansi.CYAN, enabled=self.use_color)}: {words}")
            return "\n".join(lines) if lines else "No anagram groups found."

        if result.multi_word_matches:
            return "\n".join(" ".join(word.original for word in match) for match in result.multi_word_matches)

        if result.matches:
            return "\n".join(word.original for word in result.matches)

        return "No matches found."
