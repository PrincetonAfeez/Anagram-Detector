"""Configuration loading for ~/.anagram/config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from anagram_detector.cache import default_cache_dir


@dataclass(frozen=True, slots=True)
class Config:
    """Configuration for the anagram detector."""
    language: str = "en"
    strategy: str = "sorted"
    output_format: str = "plain"
    cache_dir: Path = default_cache_dir()
    normalizers: tuple[str, ...] = (
        "casefold",
        "whitespace",
        "punctuation",
        "diacritics",
        "nonalpha",
    )


def load_config(path: Path | None = None) -> Config:
    """Load configuration from a file."""
    config_path = path or Path.home() / ".anagram" / "config.toml"
    if not config_path.exists():
        return Config()

    with config_path.open("rb") as file:
        data = tomllib.load(file)

    defaults = Config()
    normalizers = tuple(data.get("normalizers", defaults.normalizers))
    cache_dir = Path(data.get("cache_dir", defaults.cache_dir)).expanduser()
    return Config(
        language=str(data.get("language", defaults.language)),
        strategy=str(data.get("strategy", defaults.strategy)),
        output_format=str(data.get("format", defaults.output_format)),
        cache_dir=cache_dir,
        normalizers=normalizers,
    )
