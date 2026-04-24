from __future__ import annotations

import functools
import hashlib
import pickle
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar, cast

P = ParamSpec("P")
T = TypeVar("T")

def default_cache_dir() -> Path:
    return Path.home() / ".anagram" / "cache"

def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def file_content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
