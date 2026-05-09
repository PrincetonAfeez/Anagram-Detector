"""Small disk cache utilities.

There is intentionally no eviction policy. Cache keys include a dictionary content hash, so
source changes create fresh files and old cache files remain until `anagram cache clear`.
"""

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
    """Get the default cache directory."""
    return Path.home() / ".anagram" / "cache"


def stable_hash(text: str) -> str:
    """Compute a stable hash of the text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_content_hash(path: Path) -> str:
    """Compute a hash of the file's content."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def disk_cached(path_builder: Callable[P, Path]) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Cache a pure function to disk using a path computed from its arguments."""
    def decorator(function: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            path = path_builder(*args, **kwargs)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                with path.open("rb") as file:
                    return cast(T, pickle.load(file))  # noqa: S301 - local cache of our own objects.

            value = function(*args, **kwargs)
            temporary = path.with_suffix(path.suffix + ".tmp")
            with temporary.open("wb") as file:
                pickle.dump(value, file, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.replace(path)
            return value

        return wrapper

    return decorator


def cache_info(cache_dir: Path | None = None) -> dict[str, int]:
    """Get information about the cache."""
    directory = cache_dir or default_cache_dir()
    files = list(directory.glob("*.pickle")) if directory.exists() else []
    return {
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
    }


def clear_cache(cache_dir: Path | None = None) -> int:
    """Remove all cache files."""
    directory = cache_dir or default_cache_dir()
    if not directory.exists():
        return 0
    count = len(list(directory.glob("*")))
    shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return count
