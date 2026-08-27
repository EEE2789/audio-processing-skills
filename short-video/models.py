"""Data type definitions for short video pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


CoinType = Literal["BTC", "ETH"]


@dataclass
class ClipCandidate:
    """A single clip selected by LLM for short video rendering."""

    coin: CoinType
    start: str  # HH:MM:SS.mmm
    end: str  # HH:MM:SS.mmm
    duration_seconds: float
    title: str
    top_hook: str
    bottom_warning: str
    reason: str


@dataclass
class LlmSelectionResult:
    """Full LLM selection output."""

    video_count: int
    results: list[ClipCandidate] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of program-side validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
