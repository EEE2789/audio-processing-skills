"""Main entry point for short video pipeline.

Usage:
    python3 main.py [--video <video_path>] [--srt <srt_path>] [--output-dir <dir>]

Reads Video1 (no-subtitle 1.1x video) + SRT, calls LLM for segment selection,
validates results, and renders 1080x1920 vertical short videos.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

# Ensure skill directory is on sys.path for flat module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ClipCandidate
from timecode import get_video_duration_seconds, parse_timecode
from llm_select import select_segments
from render_clip import render_clip


def find_video1(pipeline_dir: str = "/Users/ai/Documents/video_pipeline") -> str | None:
    """Find the latest Video1 file in 2output directory."""
    output_dir = os.path.join(pipeline_dir, "2output")
    if not os.path.isdir(output_dir):
        return None
    candidates = [f for f in os.listdir(output_dir) if f.startswith("1繁体") and f.endswith(".mp4")]
    if not candidates:
        return None
    # Sort by modification time, newest first
    candidates.sort(key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)
    return os.path.join(output_dir, candidates[0])


def find_srt(pipeline_dir: str = "/Users/ai/Documents/video_pipeline") -> str | None:
    """Find the latest simplified SRT file in 3daily directory."""
    daily_dir = os.path.join(pipeline_dir, "3daily")
    if not os.path.isdir(daily_dir):
        return None
    candidates = [f for f in os.listdir(daily_dir) if f.startswith("简体") and f.endswith(".srt")]
    if not candidates:
        return None
    candidates.sort(key=lambda f: os.path.getmtime(os.path.join(daily_dir, f)), reverse=True)
    return os.path.join(daily_dir, candidates[0])


def find_timeline(pipeline_dir: str = "/Users/ai/Documents/video_pipeline") -> str | None:
    """Find the assets timeline JSON file in 3daily directory."""
    daily_dir = os.path.join(pipeline_dir, "3daily")
    timeline_path = os.path.join(daily_dir, "assets_timeline.json")
    if os.path.exists(timeline_path):
        return timeline_path
    return None


def generate_output_name(clip: ClipCandidate, output_dir: str) -> str:
    """Generate output filename: YYYY-MM-DD_COIN_HHMMSS.mp4"""
    today = date.today().strftime("%Y-%m-%d")
    start_sec = parse_timecode(clip.start)
    mm = int(start_sec // 60) % 60
    ss = int(start_sec % 60)
    filename = f"{today}_{clip.coin}_{mm:02d}{ss:02d}.mp4"
    return os.path.join(output_dir, filename)


def run_pipeline(
    video_path: str,
    srt_path: str,
    output_dir: str,
    timeline_path: str | None = None,
) -> list[str]:
    """Run the complete short video pipeline.

    Args:
        video_path: Path to Video1
        srt_path: Path to SRT file
        output_dir: Output directory
        timeline_path: Optional path to assets_timeline.json

    Returns:
        List of output file paths.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get video duration for boundary validation
    print(f"[MAIN] Source video: {video_path}")
    print(f"[MAIN] SRT file: {srt_path}")
    if timeline_path:
        print(f"[MAIN] Timeline file: {timeline_path}")
    video_duration = get_video_duration_seconds(video_path)
    print(f"[MAIN] Video duration: {video_duration:.1f}s")

    # Step 1: LLM selection
    print("\n[MAIN] === Step 1: LLM Segment Selection ===")
    selection = select_segments(
        srt_path,
        video_duration_seconds=video_duration,
        timeline_path=timeline_path,
    )
    print(f"[MAIN] video_count: {selection.video_count}")

    if selection.video_count == 0:
        print("[MAIN] No suitable segments found. Exiting.")
        return []

    # Step 2: Render each clip
    print(f"\n[MAIN] === Step 2: Rendering {selection.video_count} clip(s) ===")
    output_files = []
    for clip in selection.results:
        output_path = generate_output_name(clip, output_dir)
        print(f"\n[MAIN] --- Rendering {clip.coin} clip ---")
        rendered = render_clip(video_path, srt_path, output_path, clip)
        output_files.append(rendered)

    # Summary
    print(f"\n[MAIN] === Done! {len(output_files)} video(s) rendered ===")
    for f in output_files:
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f"  -> {f} ({size_mb:.1f}MB)")

    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Short video pipeline: LLM selection + FFmpeg rendering"
    )
    parser.add_argument("--video", help="Path to Video1 (1.1x horizontal video)")
    parser.add_argument("--srt", help="Path to SRT subtitle file")
    parser.add_argument("--timeline", help="Path to assets_timeline.json")
    parser.add_argument("--output-dir", default="/Users/ai/Documents/video_pipeline/2output",
                        help="Output directory for short videos")
    args = parser.parse_args()

    # Auto-detect files if not specified
    video_path = args.video or find_video1()
    srt_path = args.srt or find_srt()
    timeline_path = args.timeline or find_timeline()

    if not video_path:
        print("Error: No Video1 found. Use --video to specify.", file=sys.stderr)
        sys.exit(1)
    if not srt_path:
        print("Error: No SRT file found. Use --srt to specify.", file=sys.stderr)
        sys.exit(1)

    run_pipeline(video_path, srt_path, args.output_dir, timeline_path)


if __name__ == "__main__":
    main()
