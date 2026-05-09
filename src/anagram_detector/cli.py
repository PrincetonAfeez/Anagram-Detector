"""Command line interface."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path

from anagram_detector.cache import cache_info, clear_cache
from anagram_detector.config import Config, load_config
from anagram_detector.engine import AnagramDetector
from anagram_detector.errors import AnagramError
from anagram_detector.formatters import formatter_from_name
from anagram_detector.normalization import NormalizationPipeline, default_pipeline, pipeline_from_names
from anagram_detector.repositories import (
    BundledDictionaryRepository,
    DictionaryRepository,
    FileDictionaryRepository,
)
from anagram_detector.signatures import (
    SignatureStrategy,
    SortedSignature,
    available_strategy_names,
    strategy_from_name,
)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    try:
        return _dispatch(args, config)
    except AnagramError as exc:
        print(f"anagram: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"anagram: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"anagram: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, config: Config) -> int:
    """Dispatch the command."""
    if args.command == "cache":
        cache_dir = Path(args.cache_dir or config.cache_dir).expanduser()
        if args.cache_command == "info":
            info = cache_info(cache_dir)
            print(f"{info['files']} files, {info['bytes']} bytes")
            return 0
        if args.cache_command == "clear":
            removed = clear_cache(cache_dir)
            print(f"Removed {removed} cached item(s).")
            return 0

    pipeline = _build_pipeline(args, config)
    strategy_name = args.strategy or config.strategy
    strategy = strategy_from_name(strategy_name)
    repository = _build_repository(args, config, pipeline, strategy)
    detector = _build_detector(args, config, repository, pipeline, strategy)
    formatter = formatter_from_name(args.output_format or config.output_format, no_color=args.no_color)

    if args.command == "check":
        result = detector.check(_read_text_arg(args.first), _read_text_arg(args.second))
    elif args.command == "find":
        result = detector.find_exact(_read_text_arg(args.text))
    elif args.command == "sub":
        result = detector.find_subanagrams(_read_text_arg(args.text))
    elif args.command == "multi":
        result = detector.find_multi_word(
            _read_text_arg(args.text),
            max_words=args.max_words,
            max_results=args.max_results,
        )
    elif args.command == "group":
        result = detector.group_words(_read_lines_arg(args.source))
    elif args.command == "bench":
        _run_benchmark(args, config, pipeline)
        return 0
    else:
        raise ValueError("No command supplied.")

    print(formatter.format(result))
    return 0


def _build_detector(
    args: argparse.Namespace,
    config: Config,
    repository: DictionaryRepository,
    pipeline: NormalizationPipeline,
    strategy: SignatureStrategy,
) -> AnagramDetector:
    """Build the anagram detector."""
    return AnagramDetector(
        repository,
        pipeline,
        strategy,
        cache_dir=Path(args.cache_dir or config.cache_dir).expanduser(),
        min_length=args.min_length,
    )


def _build_repository(
    args: argparse.Namespace,
    config: Config,
    pipeline: NormalizationPipeline,
    strategy: SignatureStrategy,
) -> DictionaryRepository:
    if args.dictionary:
        """Build the dictionary repository."""
        return FileDictionaryRepository(Path(args.dictionary), pipeline, strategy)
    return BundledDictionaryRepository(args.language or config.language, pipeline, strategy)


def _build_pipeline(args: argparse.Namespace, config: Config) -> NormalizationPipeline:
    """Build the normalization pipeline."""
    if args.no_diacritics:
        normalizers = tuple(name for name in config.normalizers if name != "diacritics")
        return pipeline_from_names(normalizers)
    if config.normalizers:
        return pipeline_from_names(config.normalizers)
    return default_pipeline()


def _run_benchmark(
    args: argparse.Namespace,
    config: Config,
    pipeline: NormalizationPipeline,
) -> None:
    """Run the benchmark."""
    raw_strategy = SortedSignature()
    repository = _build_repository(args, config, pipeline, raw_strategy)
    normalized_words = [pipeline.normalize(word) for word in repository.raw_words()]
    normalized_words = [word for word in normalized_words if word]
    print(f"words,{len(normalized_words)}")
    for strategy_name in available_strategy_names():
        strategy = strategy_from_name(strategy_name)
        started = time.perf_counter()
        for word in normalized_words:
            strategy.signature(word)
        elapsed_ms = (time.perf_counter() - started) * 1000
        print(f"{strategy_name},{elapsed_ms:.3f}")


def _read_text_arg(value: str) -> str:
    """Read text from a file or stdin."""
    if value == "-":
        return sys.stdin.read()
    return value


def _read_lines_arg(value: str) -> list[str]:
    """Read lines from a file or stdin."""
    if value == "-":
        return sys.stdin.read().splitlines()
    with Path(value).expanduser().open("r", encoding="utf-8") as file:
        return file.readlines()


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(prog="anagram", description="Detect and search for anagrams.")
    parser.add_argument("--language", default=None, help="Bundled dictionary language code.")
    parser.add_argument("--dictionary", default=None, help="Path to a dictionary file.")
    parser.add_argument(
        "--strategy",
        choices=available_strategy_names(),
        default=None,
        help="Signature strategy.",
    )
    parser.add_argument("--no-diacritics", action="store_true", help="Disable diacritic folding.")
    parser.add_argument(
        "--min-length",
        type=_int_at_least(1, "min-length"),
        default=1,
        help="Minimum dictionary word length.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("plain", "json", "csv"),
        default=None,
        help="Output format.",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color.")
    parser.add_argument("--cache-dir", default=None, help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check whether two inputs are anagrams.")
    check.add_argument("first")
    check.add_argument("second")

    find = subparsers.add_parser("find", help="Find exact dictionary anagrams.")
    find.add_argument("text")

    sub = subparsers.add_parser("sub", help="Find dictionary words formable from input letters.")
    sub.add_argument("text")

    multi = subparsers.add_parser("multi", help="Find multi-word anagrams.")
    multi.add_argument("text")
    multi.add_argument("--max-words", type=_int_at_least(2, "max-words"), default=3)
    multi.add_argument("--max-results", type=_int_at_least(1, "max-results"), default=100)

    group = subparsers.add_parser("group", help="Group words from a file or stdin.")
    group.add_argument("source", help="File path, or - for stdin.")

    subparsers.add_parser("bench", help="Benchmark signature strategies.")

    cache = subparsers.add_parser("cache", help="Manage disk cache.")
    cache_subparsers = cache.add_subparsers(dest="cache_command", required=True)
    cache_subparsers.add_parser("info", help="Show cache info.")
    cache_subparsers.add_parser("clear", help="Clear cache files.")

    return parser


def _int_at_least(minimum: int, label: str) -> Callable[[str], int]:
    """Parse an integer at least as specified."""
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{label} must be an integer.") from exc
        if parsed < minimum:
            raise argparse.ArgumentTypeError(f"{label} must be >= {minimum}.")
        return parsed

    return parse
