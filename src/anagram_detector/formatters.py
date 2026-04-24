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


class JSONFormatter:
    def format(self, result: MatchResult) -> str:
        return json.dumps(_result_to_json(result), ensure_ascii=False, indent=2)


class CSVFormatter:
    def format(self, result: MatchResult) -> str:
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
    if name == "plain":
        return PlainFormatter(use_color=color_enabled(no_color))
    if name == "json":
        return JSONFormatter()
    if name == "csv":
        return CSVFormatter()
    raise ValueError(f"Unknown format '{name}'.")
