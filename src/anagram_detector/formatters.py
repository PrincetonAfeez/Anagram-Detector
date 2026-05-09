"""Output formatters."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any, Protocol

from anagram_detector.colors import Ansi, color_enabled, paint
from anagram_detector.models import AnagramGroup, MatchResult, Word


class OutputFormatter(Protocol):
    """Format a match result for display."""

    def format(self, result: MatchResult) -> str:
        """Return display text."""


@dataclass(frozen=True, slots=True)
class PlainFormatter:
    """Format a match result as plain text."""

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


class JSONFormatter:
    def format(self, result: MatchResult) -> str:
        """Format a match result as JSON."""
        return json.dumps(_result_to_json(result), ensure_ascii=False, indent=2)


class CSVFormatter:
    """Format a match result as CSV."""

    def format(self, result: MatchResult) -> str:
        """Format a match result as CSV."""
        output = io.StringIO()
        if result.is_match is not None:
            writer = csv.DictWriter(
                output,
                fieldnames=["query", "compared_to", "is_match", "elapsed_ms"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "query": result.query,
                    "compared_to": result.compared_to,
                    "is_match": result.is_match,
                    "elapsed_ms": f"{result.elapsed_ms:.3f}",
                }
            )
            return output.getvalue().strip()

        if result.groups:
            writer = csv.DictWriter(output, fieldnames=["signature", "words"])
            writer.writeheader()
            for group in result.groups:
                writer.writerow(
                    {
                        "signature": str(group.signature),
                        "words": " ".join(word.original for word in _sorted_words(group.words)),
                    }
                )
            return output.getvalue().strip()

        if result.multi_word_matches:
            writer = csv.DictWriter(output, fieldnames=["query", "words"])
            writer.writeheader()
            for match in result.multi_word_matches:
                writer.writerow({"query": result.query, "words": " ".join(word.original for word in match)})
            return output.getvalue().strip()

        writer = csv.DictWriter(output, fieldnames=["query", "match_type", "word", "normalized"])
        writer.writeheader()
        for word in result.matches:
            writer.writerow(
                {
                    "query": result.query,
                    "match_type": result.match_type.value,
                    "word": word.original,
                    "normalized": word.normalized,
                }
            )
        return output.getvalue().strip()


def formatter_from_name(name: str, *, no_color: bool = False) -> OutputFormatter:
    """Resolve a formatter by CLI/config name."""
    if name == "plain":
        return PlainFormatter(use_color=color_enabled(no_color))
    if name == "json":
        return JSONFormatter()
    if name == "csv":
        return CSVFormatter()
    raise ValueError(f"Unknown format '{name}'.")


def _result_to_json(result: MatchResult) -> dict[str, Any]:
    """Convert a match result to JSON."""
    return {
        "query": result.query,
        "match_type": result.match_type.value,
        "matches": [_word_to_json(word) for word in result.matches],
        "multi_word_matches": [
            [_word_to_json(word) for word in match] for match in result.multi_word_matches
        ],
        "groups": [_group_to_json(group) for group in result.groups],
        "compared_to": result.compared_to,
        "is_match": result.is_match,
        "total_candidates_searched": result.total_candidates_searched,
        "elapsed_ms": round(result.elapsed_ms, 3),
    }


def _word_to_json(word: Word) -> dict[str, str]:
    """Convert a word to JSON."""
    return {
        "original": word.original,
        "normalized": word.normalized,
        "signature": str(word.signature),
    }


def _group_to_json(group: AnagramGroup) -> dict[str, Any]:
    """Convert an anagram group to JSON."""
    return {
        "signature": str(group.signature),
        "words": [_word_to_json(word) for word in _sorted_words(group.words)],
    }


def _sorted_words(words: frozenset[Word]) -> tuple[Word, ...]:
    """Sort words by original string case-folded."""
    return tuple(sorted(words, key=lambda word: word.original.casefold()))
