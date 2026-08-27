#!/usr/bin/env python3
"""
基于 Video4 剪辑各币种/股票独立视频

包含：
- 开头介绍（00:00 - 00:04.700）
- 该币种/股票的独立内容
- 无封面
"""

import sys
import os
import subprocess
import re
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# ====== 配置 ======
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
VIDEO4_DIR = "/Users/ai/Documents/video_pipeline/2output"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"

VIDEO_CODEC = "libx264"
PIXEL_FMT = "yuv420p"
PROFILE = "high"
LEVEL = "4.2"
CRF = "15"
PRESET = "veryfast"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "320k"

INTRO_END = 4.7  # 开头介绍结束时间（秒）


def get_video4():
    """获取 Video4 文件"""
    import glob

    video4_pattern = os.path.join(VIDEO4_DIR, "4字幕*.mp4")
    video4_files = glob.glob(video4_pattern)

    if not video4_files:
        raise RuntimeError(f"❌ 在 {VIDEO4_DIR} 中未找到 Video4")

    video4_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return video4_files[0]


def time_to_seconds(time_str):
    """将时间码转换为秒

    支持格式：
    - "00:02:49,960" (SRT格式)
    - "2:50" (简化格式)
    - "171.56" (纯数字)
    """
    if ',' in time_str:
        # SRT 格式: 00:02:49,960
        parts = time_str.split(',')
        time_part = parts[0]
        ms = int(parts[1]) / 1000
        h, m, s = map(int, time_part.split(':'))
        return h * 3600 + m * 60 + s + ms
    elif ':' in time_str:
        # 简化格式: 2:50
        parts = time_str.split(':')
        if len(parts) == 2:
            m, s = map(float, parts)
            return m * 60 + s
        elif len(parts) == 3:
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
    else:
        # 纯数字: 171.56
        return float(time_str)


def extract_clip(video_path, start_ms, end_ms, output_path):
    """提取视频片段"""
    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-ss", f"{start_ms / 1000:.3f}",
        "-t", f"{(end_ms - start_ms) / 1000:.3f}",
        "-c:v", VIDEO_CODEC,
        "-profile:v", PROFILE,
        "-level", LEVEL,
        "-crf", CRF,
        "-preset", PRESET,
        "-pix_fmt", PIXEL_FMT,
        "-c:a", AUDIO_CODEC,
        "-b:a", AUDIO_BITRATE,
        "-y", output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def concat_videos(video_files, output_path):
    """拼接多个视频"""
    temp_dir = tempfile.mkdtemp()

    try:
        # 创建 concat 文件
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for video in video_files:
                f.write(f"file '{video}'\n")

        cmd = [
            FFMPEG_PATH, "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", VIDEO_CODEC,
            "-profile:v", PROFILE,
            "-level", LEVEL,
            "-crf", CRF,
            "-preset", PRESET,
            "-pix_fmt", PIXEL_FMT,
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_coin_video(video4_path, coin_name, start_time, end_time):
    """生成单个币种/股票的视频

    Args:
        video4_path: Video4 文件路径
        coin_name: 币种/股票名称
        start_time: 该币种内容开始时间（秒）
        end_time: 该币种内容结束时间（秒）
    """
    print(f"\n📝 正在生成 {coin_name} 视频...")

    intro_end_ms = int(INTRO_END * 1000)
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)

    temp_dir = tempfile.mkdtemp()

    try:
        # 提取开头介绍
        intro_file = os.path.join(temp_dir, "intro.mp4")
        extract_clip(video4_path, 0, intro_end_ms, intro_file)

        # 提取币种内容
        content_file = os.path.join(temp_dir, "content.mp4")
        extract_clip(video4_path, start_ms, end_ms, content_file)

        # 拼接视频
        today = datetime.now()
        month_day = today.strftime("%m.%d")
        output_filename = f"{month_day}{coin_name}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        concat_videos([intro_file, content_file], output_path)

        print(f"✅ {coin_name} 视频生成成功!")
        print(f"📁 输出文件: {output_path}")
        print(f"\n📊 时间信息:")
        print(f"   - 开头介绍: 0s - {INTRO_END}s")
        print(f"   - {coin_name}内容: {start_time}s - {end_time}s")

        return output_path

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_video4_duration(video_path):
    """获取视频总时长"""
    cmd = [FFMPEG_PATH, "-i", video_path, "-hide_banner"]
    result = subprocess.run(cmd, capture_output=True)
    output = result.stderr.decode('utf-8')

    duration_ms = None
    for line in output.split('\n'):
        if 'Duration:' in line:
            match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
            if match:
                h, m, s, ms = match.groups()
                duration_ms = ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms) * 10
                break

    return duration_ms / 1000 if duration_ms else None


def main():
    # 币种和股票配置（根据字幕分析）
    # 6月12日视频实际分析的资产
    coins = [
        {"name": "以太坊", "start": "00:02:22,560", "end": "00:03:26,240"},
        {"name": "英特尔", "start": "00:03:35,200", "end": "00:04:09,560"},
        {"name": "美光", "start": "00:04:12,600", "end": None},  # 到视频结束
    ]

    # 获取 Video4
    video4_path = get_video4()
    print(f"✅ 找到 Video4: {video4_path}")

    # 获取视频总时长
    total_duration = get_video4_duration(video4_path)
    print(f"📊 视频总时长: {total_duration:.2f}秒")

    # 生成每个币种/股票的视频
    for coin in coins:
        if coin["end"] is None:
            end_time = total_duration
        else:
            end_time = time_to_seconds(coin["end"])

        start_time = time_to_seconds(coin["start"])

        generate_coin_video(video4_path, coin["name"], start_time, end_time)

    print(f"\n✅ 所有视频生成完成!")


if __name__ == "__main__":
    main()
