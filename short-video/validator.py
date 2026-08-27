"""Program-side validation for LLM selection results."""

from __future__ import annotations

import math
from typing import Any

from models import ClipCandidate, LlmSelectionResult, ValidationResult
from timecode import is_valid_timecode, parse_timecode

ALLOWED_COINS = {"BTC", "ETH"}
REQUIRED_KEYS = [
    "coin", "start", "end", "duration_seconds",
    "title", "top_hook", "bottom_warning", "reason",
]


def validate_llm_selection(
    data: Any,
    *,
    video_duration_seconds: float | None = None,
) -> ValidationResult:
    """Validate raw LLM JSON output and return structured result."""
    errors: list[str] = []
    warnings: list[str] = []

    # --- Structure validation ---
    if not isinstance(data, dict):
        return ValidationResult(valid=False, errors=["Top-level JSON must be an object"])

    video_count = data.get("video_count")
    results = data.get("results")

    if video_count not in (0, 1, 2):
        errors.append("video_count must be 0, 1, or 2")

    if not isinstance(results, list):
        errors.append("results must be an array")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    if isinstance(video_count, int) and len(results) != video_count:
        errors.append("results length must equal video_count")

    # --- Per-item validation ---
    seen_coins: set[str] = set()

    for idx, item in enumerate(results):
        prefix = f"results[{idx}]"

        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        # Missing fields
        for key in REQUIRED_KEYS:
            if key not in item:
                errors.append(f"{prefix} missing field: {key}")

        coin = item.get("coin")
        start = item.get("start")
        end = item.get("end")
        duration_seconds = item.get("duration_seconds")
        title = item.get("title")
        top_hook = item.get("top_hook")
        bottom_warning = item.get("bottom_warning")
        reason = item.get("reason")

        # Coin validation
        if coin not in ALLOWED_COINS:
            errors.append(f"{prefix}.coin must be BTC or ETH")
        else:
            if coin in seen_coins:
                errors.append(f"Duplicate coin in results: {coin}")
            seen_coins.add(coin)

        # Timecode format
        if not isinstance(start, str) or not is_valid_timecode(start):
            errors.append(f"{prefix}.start invalid format")
        if not isinstance(end, str) or not is_valid_timecode(end):
            errors.append(f"{prefix}.end invalid format")

        # Duration validation
        if not isinstance(duration_seconds, (int, float)) or not math.isfinite(duration_seconds):
            errors.append(f"{prefix}.duration_seconds invalid")
        elif duration_seconds <= 0:
            errors.append(f"{prefix}.duration_seconds must be > 0")

        # Text fields non-empty
        for key, value in [("title", title), ("top_hook", top_hook),
                           ("bottom_warning", bottom_warning), ("reason", reason)]:
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{key} empty")

        # Time-based calculations (only if timecodes valid)
        if (isinstance(start, str) and isinstance(end, str)
                and is_valid_timecode(start) and is_valid_timecode(end)):
            start_sec = parse_timecode(start)
            end_sec = parse_timecode(end)
            actual_duration = end_sec - start_sec

            if end_sec <= start_sec:
                errors.append(f"{prefix} end must be later than start")

            # Duration hard limits
            if actual_duration < 12 or actual_duration > 45:
                errors.append(f"{prefix} duration outside hard limit (12-45s)")
            elif actual_duration < 20 or actual_duration > 35:
                warnings.append(f"{prefix} duration outside recommended 20-35s range")

            # Duration consistency
            if isinstance(duration_seconds, (int, float)) and math.isfinite(duration_seconds):
                diff = abs(actual_duration - float(duration_seconds))
                if diff > 1.0:
                    errors.append(f"{prefix} duration_seconds differs too much from end-start")
                elif diff > 0.5:
                    warnings.append(f"{prefix} duration_seconds differs from end-start")

            # Video boundary check
            if (isinstance(video_duration_seconds, (int, float))
                    and end_sec > float(video_duration_seconds)):
                errors.append(f"{prefix} exceeds source video duration")

        # Title-coin consistency warning
        if isinstance(title, str) and isinstance(coin, str) and coin in ALLOWED_COINS:
            if coin not in title:
                warnings.append(f"{prefix} title does not include coin symbol")

    # --- Cross-item validation ---
    if video_count == 2 and seen_coins and seen_coins != {"BTC", "ETH"}:
        errors.append("When video_count is 2, results must include BTC and ETH")

    # --- Overlap warning ---
    if len(results) == 2:
        r0, r1 = results[0], results[1]
        if (isinstance(r0.get("start"), str) and isinstance(r0.get("end"), str)
                and isinstance(r1.get("start"), str) and isinstance(r1.get("end"), str)
                and all([
                    is_valid_timecode(r0.get("start")),
                    is_valid_timecode(r0.get("end")),
                    is_valid_timecode(r1.get("start")),
                    is_valid_timecode(r1.get("end")),
                ])):
            s0, e0 = parse_timecode(r0["start"]), parse_timecode(r0["end"])
            s1, e1 = parse_timecode(r1["start"]), parse_timecode(r1["end"])
            overlap_start = max(s0, s1)
            overlap_end = min(e0, e1)
            if overlap_start < overlap_end:
                overlap = overlap_end - overlap_start
                shorter = min(e0 - s0, e1 - s1)
                if shorter > 0 and overlap / shorter > 0.6:
                    warnings.append("Two results have high time overlap (>60%)")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def parse_to_selection(data: dict) -> LlmSelectionResult:
    """Convert validated JSON dict to typed LlmSelectionResult."""
    results = []
    for item in data.get("results", []):
        results.append(ClipCandidate(
            coin=item["coin"],
            start=item["start"],
            end=item["end"],
            duration_seconds=float(item["duration_seconds"]),
            title=item["title"],
            top_hook=item["top_hook"],
            bottom_warning=item["bottom_warning"],
            reason=item["reason"],
        ))
    return LlmSelectionResult(
        video_count=int(data["video_count"]),
        results=results,
    )
