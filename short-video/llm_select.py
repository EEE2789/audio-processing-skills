"""DeepSeek LLM integration for short video segment selection."""

from __future__ import annotations

import json
import os
import re

import requests

from models import LlmSelectionResult
from validator import parse_to_selection, validate_llm_selection
from retry_prompt import build_retry_prompt, should_retry

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_RETRIES = 2

# Default .env path (same location as other skills)
_DEFAULT_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def parse_srt_time(time_str: str) -> float:
    """Parse SRT timecode to seconds."""
    # Format: HH:MM:SS,mmm
    match = re.match(r'(\d+):(\d+):(\d+),(\d+)', time_str)
    if match:
        h, m, s, ms = match.groups()
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return 0.0


def filter_srt_by_coin(srt_content: str, coin: str, start_ms: int, end_ms: int) -> str:
    """Filter SRT content to only include subtitles for a specific coin and time range.

    Args:
        srt_content: Full SRT content
        coin: Coin name (BTC, ETH, etc.)
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds

    Returns:
        Filtered SRT content
    """
    start_sec = start_ms / 1000
    end_sec = end_ms / 1000

    blocks = srt_content.strip().split('\n\n')
    filtered_blocks = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            # Parse time range: "00:01:23,456 --> 00:01:26,789"
            match = re.match(r'(\d{2}:\d{2}:\d+,\d{3})\s*-->\s*(\d{2}:\d{2}:\d+,\d{3})', time_line)
            if match:
                start_str, end_str = match.groups()
                block_start = parse_srt_time(start_str)
                block_end = parse_srt_time(end_str)

                # Check if this block overlaps with the coin's time range
                if block_end >= start_sec and block_start <= end_sec:
                    filtered_blocks.append(block)

    return '\n\n'.join(filtered_blocks)


def get_timeline_for_coin(timeline_path: str, coin: str) -> tuple[int, int] | None:
    """Get time range for a coin from assets_timeline.json.

    Args:
        timeline_path: Path to assets_timeline.json
        coin: Coin name to look up

    Returns:
        (start_ms, end_ms) or None if not found
    """
    with open(timeline_path) as f:
        data = json.load(f)

    # Support both 'assets' and 'segments' keys
    for asset in data.get('assets', []) or data.get('segments', []):
        asset_name = asset.get('name', '')
        # Match BTC/Bitcoin, ETH/Ethereum
        if (coin == 'BTC' and asset_name in ['比特币', 'BTC']) or \
           (coin == 'ETH' and asset_name in ['以太坊', 'ETH']):
            return (asset.get('start_ms', 0), asset.get('end_ms', 0))

    return None


def load_timeline_filtered_srt(srt_path: str, timeline_path: str) -> str:
    """Load SRT content and create filtered versions for BTC and ETH.

    Args:
        srt_path: Path to SRT file
        timeline_path: Path to assets_timeline.json

    Returns:
        Modified SRT content with coin-specific sections
    """
    with open(srt_path) as f:
        srt_content = f.read()

    # Get time ranges for BTC and ETH
    btc_range = get_timeline_for_coin(timeline_path, 'BTC')
    eth_range = get_timeline_for_coin(timeline_path, 'ETH')

    if not btc_range and not eth_range:
        # No timeline data found, return original
        print("[LLM] No timeline data found, using full SRT")
        return srt_content

    # Create filtered sections
    sections = []

    # Add intro section (before first coin)
    blocks = srt_content.strip().split('\n\n')
    if blocks:
        first_block = blocks[0]
        match = re.search(r'(\d{2}:\d{2}:\d+,\d{3})', first_block)
        if match:
            first_start = parse_srt_time(match.group(1))
            if btc_range:
                btc_start = btc_range[0] / 1000
                if first_start < btc_start - 5:  # Allow 5s gap
                    sections.append(f"[开头介绍 - 到 {btc_range[0]/1000:.1f}s]")
                    sections.append(filter_srt_by_coin(srt_content, 'BTC', 0, btc_range[0]))

    # Add BTC section
    if btc_range:
        sections.append(f"\n[BTC分析 - {btc_range[0]/1000:.1f}s 到 {btc_range[1]/1000:.1f}s]")
        sections.append(filter_srt_by_coin(srt_content, 'BTC', btc_range[0], btc_range[1]))

    # Add ETH section
    if eth_range:
        sections.append(f"\n[ETH分析 - {eth_range[0]/1000:.1f}s 到 {eth_range[1]/1000:.1f}s]")
        sections.append(filter_srt_by_coin(srt_content, 'ETH', eth_range[0], eth_range[1]))

    result = '\n'.join(sections)
    print(f"[LLM] Loaded SRT with timeline filtering (BTC: {btc_range}, ETH: {eth_range})")
    return result


def _load_api_key(env_path: str | None = None) -> str:
    """Load DeepSeek API key from .env file."""
    path = env_path or _DEFAULT_ENV_PATH
    if not os.path.exists(path):
        # Fallback: check ethereum-extract .env
        fallback = os.path.expanduser("~/.claude/skills/ethereum-extract/.env")
        if os.path.exists(fallback):
            path = fallback
        else:
            raise FileNotFoundError(f"API key file not found: {path}")

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise ValueError("DEEPSEEK_API_KEY not found in .env file")


def _load_system_prompt() -> str:
    """Load the LLM selection prompt from the Obsidian vault doc."""
    prompt_path = os.path.expanduser(
        "~/Documents/Obsidian Vault/3.军长视频/短视频/短视频选段提示词.md"
    )
    if os.path.exists(prompt_path):
        with open(prompt_path) as f:
            content = f.read()
        return content.strip()
    raise FileNotFoundError(f"Prompt file not found: {prompt_path}")


def call_llm(system_prompt: str, user_message: str, api_key: str) -> str:
    """Call DeepSeek API and return raw text response."""
    try:
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "temperature": 0.7,
                "max_tokens": 3000,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        if "choices" not in result or len(result["choices"]) == 0:
            print(f"[LLM] API Response missing choices: {result}")
            raise RuntimeError("API returned no choices")
        return result["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"[LLM] Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[LLM] Response status: {e.response.status_code}")
            print(f"[LLM] Response body: {e.response.text[:500]}")
        raise


def select_segments(
    srt_path: str,
    *,
    video_duration_seconds: float | None = None,
    env_path: str | None = None,
    timeline_path: str | None = None,
) -> LlmSelectionResult:
    """Run LLM selection with retry logic.

    Args:
        srt_path: Path to the SRT subtitle file.
        video_duration_seconds: Optional video duration for boundary validation.
        env_path: Optional path to .env file with API key.
        timeline_path: Optional path to assets_timeline.json for content filtering.

    Returns:
        Validated LlmSelectionResult.
    """
    api_key = _load_api_key(env_path)
    system_prompt = _load_system_prompt()

    # Load SRT with timeline filtering if timeline is provided
    if timeline_path and os.path.exists(timeline_path):
        srt_content = load_timeline_filtered_srt(srt_path, timeline_path)
    else:
        with open(srt_path) as f:
            srt_content = f.read()

    user_message = f"以下是视频的 SRT 字幕内容：\n\n{srt_content}"

    # First attempt
    print("[LLM] Calling DeepSeek for segment selection...")
    raw = call_llm(system_prompt, user_message, api_key)
    print(f"[LLM] Raw response length: {len(raw)} chars")

    # Parse and validate
    parsed = _parse_json(raw)
    validation = validate_llm_selection(
        parsed, video_duration_seconds=video_duration_seconds
    )

    retry_count = 0
    while should_retry(validation, retry_count):
        retry_count += 1
        print(f"[LLM] Validation failed (attempt {retry_count}), retrying...")
        for err in validation.errors:
            print(f"  [ERROR] {err}")

        retry_msg = build_retry_prompt(validation.errors)
        raw = call_llm(system_prompt, retry_msg, api_key)
        parsed = _parse_json(raw)
        validation = validate_llm_selection(
            parsed, video_duration_seconds=video_duration_seconds
        )

    if not validation.valid:
        raise RuntimeError(
            f"LLM selection failed validation after {MAX_RETRIES} retries: "
            + "; ".join(validation.errors)
        )

    for w in validation.warnings:
        print(f"  [WARN] {w}")

    return parse_to_selection(parsed)


def _parse_json(raw: str) -> dict:
    """Extract JSON from raw LLM response, handling markdown code blocks."""
    text = raw.strip()
    # Strip markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return json.loads(text)
