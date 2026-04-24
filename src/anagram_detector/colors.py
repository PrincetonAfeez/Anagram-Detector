"""Tiny ANSI color helper."""

from __future__ import annotations

import os
import sys


class Ansi:
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def color_enabled(disabled: bool = False) -> bool:
    return not disabled and "NO_COLOR" not in os.environ and sys.stdout.isatty()


def paint(text: str, color: str, *, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color}{text}{Ansi.RESET}"
