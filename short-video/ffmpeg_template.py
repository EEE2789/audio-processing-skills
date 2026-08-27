"""FFmpeg template parameters and filter graph generation."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field

from models import ClipCandidate
from timecode import parse_timecode

# --- Theme colors ---

THEMES = {
    "BTC": {
        "primary_color": "#F7931A",
        "secondary_color": "#FFB347",
    },
    "ETH": {
        "primary_color": "#627EEA",
        "secondary_color": "#8FA8FF",
    },
}


@dataclass
class TemplateConfig:
    """All layout and style parameters for the 1080x1920 vertical template."""

    # Canvas
    canvas_width: int = 1080
    canvas_height: int = 1920
    background_color: str = "#0B0D12"

    # Safe margins
    safe_margin_x: int = 72
    safe_margin_top: int = 56
    safe_margin_bottom: int = 64

    # Area heights
    top_area_height: int = 300
    middle_area_height: int = 960
    bottom_area_height: int = 660

    # Video placement
    video_width: int = 1080
    video_height: int = 608
    video_x: int = 0
    video_y: int = 622

    # Subtitle band
    subtitle_band_x: int = 72
    subtitle_band_y: int = 780
    subtitle_band_width: int = 936
    subtitle_band_height: int = 520
    subtitle_band_color: str = "black@0.68"

    # Debug mode: skip title / top_hook / bottom_warning
    subtitle_only_debug: bool = False

    # Font config (fix: use actually existing font)
    drawtext_font_file: str = "/System/Library/Fonts/Hiragino Sans GB.ttc"
    subtitle_font_name: str = "Hiragino Sans GB"
    subtitle_fonts_dir: str = "/System/Library/Fonts"

    # Title
    title_x: int = 540
    title_y: int = 162
    title_font_size: int = 72

    # Top hook
    top_hook_x: int = 540
    top_hook_y: int = 262
    top_hook_font_size: int = 76
    top_hook_max_width: int = 920

    # Bottom warning (上移以避开平台UI遮罩，距离底部至少470px)
    bottom_warning_x: int = 540
    bottom_warning_y: int = 1450  # 距离底部470px，更安全地避开平台遮罩
    bottom_warning_font_size: int = 62
    bottom_warning_max_width: int = 840

    # Subtitle style
    subtitle_font_size: int = 45
    subtitle_color: str = "&H00FFFFFF&"
    subtitle_border_color: str = "&H00000000&"
    subtitle_border_width: int = 6

    # Output
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    pix_fmt: str = "yuv420p"
    crf: int = 20
    preset: str = "medium"

    @property
    def bottom_area_y(self) -> int:
        return self.canvas_height - self.bottom_area_height

    @property
    def middle_area_y(self) -> int:
        return self.top_area_height


def get_theme(coin: str) -> dict:
    """Get theme colors for a coin type."""
    return THEMES.get(coin, THEMES["BTC"])


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("%", "%%")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    return text


def _escape_subtitle_path(path: str) -> str:
    """Escape file path for FFmpeg subtitles filter."""
    path = path.replace("\\", "\\\\")
    path = path.replace("'", "'\\''")
    path = path.replace(":", "\\:")
    return path


def _parse_srt(srt_path: str) -> list[tuple[float, float, str]]:
    """Parse SRT file, return list of (start_sec, end_sec, text) tuples."""
    with open(srt_path, encoding="utf-8") as f:
        srt_content = f.read()

    entries = []
    blocks = re.split(r"\n\s*\n", srt_content.strip())
    ts_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_match = None
        text_lines = []
        for line in lines:
            m = ts_re.match(line.strip())
            if m:
                ts_match = m
            else:
                stripped = line.strip()
                if stripped and not stripped.isdigit():
                    text_lines.append(stripped)
        if not ts_match or not text_lines:
            continue
        h1, m1, s1, ms1 = (int(ts_match.group(i)) for i in (1, 2, 3, 4))
        h2, m2, s2, ms2 = (int(ts_match.group(i)) for i in (5, 6, 7, 8))
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        text = "\n".join(text_lines)
        entries.append((start, end, text))
    return entries


def _wrap_text(text: str, max_chars: int = 18) -> str:
    """Simple Chinese text wrapping for drawtext."""
    if len(text) <= max_chars:
        return text
    mid = len(text) // 2
    break_chars = "，。、！？；："
    best = mid
    for offset in range(0, min(mid, 6)):
        for pos in [mid - offset, mid + offset]:
            if 0 < pos < len(text) and text[pos - 1] in break_chars:
                best = pos
                break
        else:
            continue
        break
    return text[:best] + "\n" + text[best:]


def _wrap_hook(text: str, max_chars: int = 8) -> str:
    """Wrap top_hook into exactly 2 lines: comma-first, then truncate to max_chars per line."""
    # Remove trailing punctuation for cleaner display
    stripped = text.rstrip("，。、！？；：,.")
    # Try splitting on first comma (Chinese or ASCII)
    for sep in ["，", ","]:
        if sep in stripped:
            idx = stripped.index(sep)
            line1 = stripped[:idx]
            line2 = stripped[idx + len(sep):]
            # Truncate each line to max_chars
            line1 = line1[:max_chars]
            line2 = line2[:max_chars]
            return line1 + "\n" + line2
    # No comma: split at max_chars
    line1 = stripped[:max_chars]
    line2 = stripped[max_chars:max_chars * 2]
    if not line2:
        line2 = line1[-max_chars // 2:]
        line1 = line1[:-max_chars // 2]
    return line1 + "\n" + line2


def _srt_to_ass(srt_path: str, cfg: TemplateConfig) -> str:
    """Convert SRT to ASS with precise positioning within subtitle band.

    This ensures subtitles are rendered ONLY within the subtitle band area,
    not relative to the full canvas.
    """
    with open(srt_path, encoding="utf-8") as f:
        srt_content = f.read()

    # Parse SRT entries (standard SRT: index, timestamp, text)
    entries = []
    blocks = re.split(r"\n\s*\n", srt_content.strip())
    ts_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_match = None
        text_lines = []
        for line in lines:
            m = ts_re.match(line.strip())
            if m:
                ts_match = m
            else:
                stripped = line.strip()
                if stripped and not stripped.isdigit():
                    text_lines.append(stripped)
        if not ts_match or not text_lines:
            continue

        h1, m1, s1, ms1 = (int(ts_match.group(i)) for i in (1, 2, 3, 4))
        h2, m2, s2, ms2 = (int(ts_match.group(i)) for i in (5, 6, 7, 8))
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        text = "\\N".join(text_lines)
        entries.append((start, end, text))

    if not entries:
        return ""

    # ASS positioning: place subtitles at the center of the subtitle band
    # ASS uses PlayRes coordinates (same as canvas: 1080x1920)
    # MarginV pushes text from the BOTTOM of the canvas upward
    # We want text centered in the subtitle band:
    #   band_top = 1004, band_bottom = 1164
    #   band_center_y = 1084
    #   So distance from bottom = 1920 - 1084 = 836
    # But MarginV in ASS is approximate; use \pos for exact placement
    band_center_x = cfg.subtitle_band_x + cfg.subtitle_band_width // 2
    band_center_y = cfg.subtitle_band_y + cfg.subtitle_band_height // 2

    ass_lines = [
        "[Script Info]",
        f"PlayResX: {cfg.canvas_width}",
        f"PlayResY: {cfg.canvas_height}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        (
            f"Default,{cfg.subtitle_font_name},{cfg.subtitle_font_size},"
            f"{cfg.subtitle_color},&H000000FF,"
            f"{cfg.subtitle_border_color},&H80000000&,"
            f"-1,0,0,0,100,100,0,0,1,"
            f"{cfg.subtitle_border_width},0,"
            f"5,0,0,0,1"
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for start, end, text in entries:
        start_h = int(start // 3600)
        start_m = int((start % 3600) // 60)
        start_s = start % 60
        end_h = int(end // 3600)
        end_m = int((end % 3600) // 60)
        end_s = end % 60

        def _fmt(h, m, s):
            return f"{h}:{m:02d}:{s:05.2f}"

        # Use \pos for exact placement within subtitle band
        # {\pos(x,y)} overrides MarginV and Alignment
        pos_tag = f"{{\\pos({band_center_x},{band_center_y})}}"
        ass_lines.append(
            f"Dialogue: 0,{_fmt(start_h,start_m,start_s)},"
            f"{_fmt(end_h,end_m,end_s)},Default,,0,0,0,,"
            f"{pos_tag}{text}"
        )

    return "\n".join(ass_lines)


def build_filter_graph(
    clip: ClipCandidate,
    srt_path: str,
    config: TemplateConfig | None = None,
) -> tuple[str, str | None]:
    """Build the complete FFmpeg filter_complex string.

    Returns:
        (filter_complex_string, ass_tmp_path_or_None)
        Caller is responsible for cleaning up ass_tmp_path after FFmpeg finishes.

    Filter layer order:
    1. [0:v] trim + scale -> [v_scaled]
    2. color background -> [base]
    3. overlay video -> [v_bg]
    4. draw subtitle band -> [v_band]
    5. draw title -> [v_top1]
    6. draw top_hook -> [v_top2]
    7. draw bottom_warning -> [v_bottom]
    8. ass subtitles -> [v_final]
    """
    cfg = config or TemplateConfig()
    theme = get_theme(clip.coin)
    title_color = "#FFB020"
    bottom_color = "#F3F4F6"

    # Generate ASS for precise subtitle band positioning
    ass_content = _srt_to_ass(srt_path, cfg)
    # Write ASS to temp file (no escaping needed for temp path)
    ass_fd, ass_tmp_path = tempfile.mkstemp(suffix=".ass")
    with os.fdopen(ass_fd, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # Compute clip duration for trim
    start_sec = parse_timecode(clip.start)
    end_sec = parse_timecode(clip.end)
    duration = end_sec - start_sec

    # Wrap long texts
    title_wrapped = _wrap_text(clip.title, 18)
    hook_wrapped = _wrap_hook(clip.top_hook, 8)
    bottom_wrapped = _wrap_text(clip.bottom_warning, 16)

    # Escape text for drawtext
    title_escaped = _escape_drawtext(title_wrapped)
    hook_escaped = _escape_drawtext(hook_wrapped)
    bottom_escaped = _escape_drawtext(bottom_wrapped)

    # Escape font path for drawtext
    font_file_escaped = cfg.drawtext_font_file.replace("'", "'\\''")

    filters = []

    # 1. Trim and scale video
    filters.append(
        f"[0:v]trim=start={start_sec}:duration={duration},"
        f"setpts=PTS-STARTPTS,"
        f"scale={cfg.video_width}:{cfg.video_height},"
        f"setsar=1[v_scaled]"
    )

    # 2. Background canvas
    filters.append(
        f"color=c={cfg.background_color}:"
        f"s={cfg.canvas_width}x{cfg.canvas_height}:"
        f"d={duration}[base]"
    )

    # 3. Overlay video onto background
    filters.append(
        f"[base][v_scaled]overlay="
        f"{cfg.video_x}:{cfg.video_y}[v_bg]"
    )

    # 4. Title, Top hook, Bottom warning
    if cfg.subtitle_only_debug:
        last_label = "v_bg"
    else:
        filters.append(
            f"[v_bg]drawtext=text='{title_escaped}':"
            f"x=(w-text_w)/2:y={cfg.title_y}:"
            f"fontsize={cfg.title_font_size}:"
            f"fontcolor={title_color}:"
            f"fontfile='{font_file_escaped}':"
            f"text_align=center[v_top1]"
        )
        filters.append(
            f"[v_top1]drawtext=text='{hook_escaped}':"
            f"x=(w-text_w)/2:y={cfg.top_hook_y}:"
            f"fontsize={cfg.top_hook_font_size}:"
            f"fontcolor=#FFB020:"
            f"fontfile='{font_file_escaped}':"
            f"text_align=center[v_top2]"
        )
        # Yellow background bar for bottom warning
        filters.append(
            f"[v_top2]drawbox=x=72:y={cfg.bottom_warning_y - 12}:"
            f"w=936:h={cfg.bottom_warning_font_size + 24}:"
            f"color=#F7C948:t=fill[v_top3]"
        )
        filters.append(
            f"[v_top3]drawtext=text='{bottom_escaped}':"
            f"x=(w-text_w)/2:y={cfg.bottom_warning_y}:"
            f"fontsize={cfg.bottom_warning_font_size}:"
            f"fontcolor=#111111:"
            f"fontfile='{font_file_escaped}':"
            f"text_align=center[v_bottom]"
        )
        last_label = "v_bottom"

    # 8. Subtitles — drawtext rendering (fontsize is actual pixels)
    srt_entries = _parse_srt(srt_path)
    clip_entries = [
        (s, e, t) for s, e, t in srt_entries
        if e > start_sec and s < end_sec
    ]

    if not clip_entries:
        filters.append(f"[{last_label}]setpts=PTS[v_final]")
    else:
        cur = last_label
        for i, (s, e, text) in enumerate(clip_entries):
            rel_start = max(0.0, s - start_sec)
            rel_end = min(e - start_sec, duration)
            if rel_start >= rel_end:
                continue

            wrapped = _wrap_text(text, 18)
            escaped = _escape_drawtext(wrapped)
            escaped = escaped.replace("\n", "\\n")

            nxt = f"v_sub{i}" if i < len(clip_entries) - 1 else "v_final"
            filters.append(
                f"[{cur}]drawtext=text='{escaped}':"
                f"x=(w-text_w)/2:y=1252:"
                f"fontsize={cfg.subtitle_font_size}:"
                f"fontcolor=white:"
                f"borderw={cfg.subtitle_border_width}:"
                f"bordercolor=black:"
                f"fontfile='{font_file_escaped}':"
                f"text_align=center:"
                f"enable='between(t,{rel_start:.3f},{rel_end:.3f})'"
                f"[{nxt}]"
            )
            cur = nxt

        if cur == last_label:
            filters.append(f"[{last_label}]setpts=PTS[v_final]")

    return ";".join(filters), ass_tmp_path


def build_ffmpeg_command(
    input_video: str,
    srt_path: str,
    output_path: str,
    clip: ClipCandidate,
    config: TemplateConfig | None = None,
) -> tuple[list[str], str | None]:
    """Build the complete FFmpeg command as a list of arguments.

    Returns:
        (command_list, ass_tmp_path_or_None)
        Caller is responsible for cleaning up ass_tmp_path after FFmpeg finishes.
    """
    cfg = config or TemplateConfig()
    filter_graph, ass_tmp_path = build_filter_graph(clip, srt_path, cfg)
    start_sec = parse_timecode(clip.start)
    end_sec = parse_timecode(clip.end)

    cmd = [
        "/opt/homebrew/bin/ffmpeg",
        "-y",
        "-i", input_video,
        "-filter_complex", filter_graph,
        "-map", "[v_final]",
        "-map", "0:a?",
        "-af", f"atrim=start={start_sec}:end={end_sec},asetpts=PTS-STARTPTS",
        "-c:v", cfg.video_codec,
        "-crf", str(cfg.crf),
        "-preset", cfg.preset,
        "-pix_fmt", cfg.pix_fmt,
        "-c:a", cfg.audio_codec,
        "-b:a", cfg.audio_bitrate,
        "-r", str(cfg.fps),
        "-movflags", "+faststart",
        "-shortest",
        output_path,
    ]

    return cmd, ass_tmp_path
