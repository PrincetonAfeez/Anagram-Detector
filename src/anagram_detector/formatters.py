from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any, Protocol

from anagram_detector.colors import Ansi, color_enabled, paint
from anagram_detector.models import AnagramGroup, MatchResult, Word

