"""FFmpeg rendering for a single short video clip."""

from __future__ import annotations

import os
import subprocess
import sys

from models import ClipCandidate
from ffmpeg_template import TemplateConfig, build_ffmpeg_command
from timecode import parse_timecode


def render_clip(
    input_video: str,
    srt_path: str,
    output_path: str,
    clip: ClipCandidate,
    config: TemplateConfig | None = None,
) -> str:
    """Render a single vertical short video clip.

    Args:
        input_video: Path to the source horizontal video (Video1).
        srt_path: Path to the SRT subtitle file.
        output_path: Path for the output video file.
        clip: ClipCandidate with timing and text info.
        config: Optional TemplateConfig override.

    Returns:
        Path to the rendered output file.
    """
    cfg = config or TemplateConfig()
    duration = parse_timecode(clip.end) - parse_timecode(clip.start)

    print(f"[RENDER] Coin: {clip.coin}")
    print(f"[RENDER] Time: {clip.start} -> {clip.end} ({duration:.1f}s)")
    print(f"[RENDER] Title: {clip.title}")
    print(f"[RENDER] Top hook: {clip.top_hook}")
    print(f"[RENDER] Bottom warning: {clip.bottom_warning}")
    print(f"[RENDER] Output: {output_path}")

    cmd, ass_tmp_path = build_ffmpeg_command(input_video, srt_path, output_path, clip, cfg)

    # Print command for debugging (truncate filter_complex for readability)
    print(f"[RENDER] FFmpeg command: ffmpeg -i {input_video} -filter_complex [...]")
    print(f"[RENDER] Running FFmpeg...")

    try:
        result = subprocess.run(
            cmd,
            shell=False,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Verify output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file not created: {output_path}")

        file_size = os.path.getsize(output_path)
        print(f"[RENDER] Done! File size: {file_size / 1024 / 1024:.1f}MB")

        return output_path
    finally:
        # Clean up ASS temp file regardless of success/failure
        if ass_tmp_path and os.path.exists(ass_tmp_path):
            os.unlink(ass_tmp_path)
