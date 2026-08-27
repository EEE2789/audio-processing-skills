"""Timecode parsing and utilities."""

from __future__ import annotations

import os
import re

TIMECODE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")


def is_valid_timecode(value: str) -> bool:
    """Check if a string matches HH:MM:SS.mmm format."""
    return bool(TIMECODE_RE.match(value))


def parse_timecode(value: str) -> float:
    """Convert HH:MM:SS.mmm to seconds."""
    if not is_valid_timecode(value):
        raise ValueError(f"Invalid timecode format: {value}")
    hh, mm, rest = value.split(":")
    ss, ms = rest.split(".")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def get_video_duration_seconds(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    import subprocess

    result = subprocess.run(
        [
            "/opt/homebrew/bin/ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            video_path,
        ],
        shell=False,
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())
