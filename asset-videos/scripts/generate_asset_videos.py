#!/usr/bin/env python3
"""
资产视频自动生成

基于资产时间轴分析结果，为每个币种生成独立视频。
"""

import sys
import os
import subprocess
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# ====== 配置 ======
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"

# 编码参数
VIDEO_CODEC = "libx264"
PIXEL_FMT = "yuv420p"
PROFILE = "high"
LEVEL = "4.2"
CRF = "15"
PRESET = "veryfast"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "320k"


def get_video4_path():
    """获取 Video4 路径"""
    import glob

    video4_pattern = os.path.join(OUTPUT_DIR, "4字幕*.mp4")
    video4_files = glob.glob(video4_pattern)

    if video4_files:
        video4_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return video4_files[0]

    raise RuntimeError(f"❌ 未找到 Video4")


def get_assets_timeline():
    """读取资产时间轴文件"""
    timeline_path = os.path.join(SUBTITLE_DIR, "assets_timeline.json")
    if not os.path.exists(timeline_path):
        raise RuntimeError(f"❌ 未找到资产时间轴文件: {timeline_path}")

    with open(timeline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_intro_time(timeline_data):
    """获取开头介绍结束时间"""
    intro = timeline_data.get('intro')
    if intro:
        return intro.get('end_ms', 4500)
    return 4500


def extract_clip(video_path, start_ms, duration_ms, output_path):
    """提取视频片段"""
    cmd = [
        FFMPEG_PATH, "-y", "-i", video_path,
        "-ss", f"{start_ms / 1000:.3f}",
        "-t", f"{duration_ms / 1000:.3f}",
        "-c:v", VIDEO_CODEC,
        "-profile:v", PROFILE,
        "-level", LEVEL,
        "-crf", CRF,
        "-preset", PRESET,
        "-pix_fmt", PIXEL_FMT,
        "-c:a", AUDIO_CODEC,
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def concat_videos(intro_path, content_path, output_path):
    """拼接开头介绍和内容"""
    # 创建 concat 文件
    concat_file = tempfile.mktemp(suffix='.txt')
    with open(concat_file, "w") as f:
        f.write(f"file '{intro_path}'\n")
        f.write(f"file '{content_path}'\n")

    cmd = [
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", VIDEO_CODEC,
        "-profile:v", PROFILE,
        "-level", LEVEL,
        "-crf", CRF,
        "-preset", PRESET,
        "-pix_fmt", PIXEL_FMT,
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # 清理临时文件
    if os.path.exists(concat_file):
        os.remove(concat_file)


def sanitize_filename(filename):
    """清理文件名"""
    invalid_chars = ['<', '>', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename


def truncate_filename_by_bytes(filename, max_bytes=250):
    """按字节长度截断文件名"""
    filename_bytes = filename.encode('utf-8')
    if len(filename_bytes) <= max_bytes:
        return filename
    truncated = filename_bytes[:max_bytes].decode('utf-8', errors='ignore')
    return truncated


def generate_asset_videos():
    """为所有资产生成独立视频"""
    print("\n📝 正在生成资产视频...")

    # 读取资产时间轴
    timeline_data = get_assets_timeline()
    segments = timeline_data.get('segments', [])
    print(f"✅ 读取资产时间轴: {len(segments)} 个段落")

    # 获取 Video4
    video4_path = get_video4_path()
    print(f"✅ 使用 Video4: {video4_path}")

    # 获取开头介绍时间
    intro_end_ms = get_intro_time(timeline_data)

    # 生成日期前缀
    today = datetime.now()
    month_day = today.strftime("%m.%d")

    temp_dir = tempfile.mkdtemp()

    try:
        # 提取开头介绍（所有视频共用）
        intro_file = os.path.join(temp_dir, "intro.mp4")
        print(f"\n📌 提取开头介绍 (0s - {intro_end_ms / 1000:.2f}s)...")
        extract_clip(video4_path, 0, intro_end_ms, intro_file)

        # 为每个资产生成视频
        # 统计每个资产出现次数，用于生成唯一文件名
        asset_counts = {}
        for seg in segments:
            asset_name = seg.get('name')
            asset_counts[asset_name] = asset_counts.get(asset_name, 0) + 1

        current_asset_index = {}  # 当前资产的第几段

        for seg in segments:
            asset_name = seg.get('name')

            # 更新当前资产索引
            current_asset_index[asset_name] = current_asset_index.get(asset_name, 0) + 1
            current_index = current_asset_index[asset_name]
            total_count = asset_counts[asset_name]

            start_ms = seg.get('start_ms')
            end_ms = seg.get('end_ms')
            duration_ms = end_ms - start_ms

            print(f"\n📌 生成 {asset_name} 视频 (第{current_index}/{total_count}段):")
            print(f"   - 时间: {seg.get('start_time')} - {seg.get('end_time')}")
            print(f"   - 时长: {duration_ms / 1000:.1f}秒")

            # 提取资产内容片段
            asset_file = os.path.join(temp_dir, f"{asset_name}.mp4")
            extract_clip(video4_path, start_ms, duration_ms, asset_file)

            # 拼接开头介绍 + 资产内容
            # 生成标题（简化版，实际应该调用 DeepSeek）
            asset_upper = asset_name.upper()

            # 如果同一资产有多段，添加序号
            if total_count > 1:
                title = f"{month_day}{asset_upper}价格今日行情({current_index})：{asset_name}行情分析（{asset_upper}合约交易）军长"
            else:
                title = f"{month_day}{asset_upper}价格今日行情：{asset_name}行情分析（{asset_upper}合约交易）军长"

            # 清理文件名
            safe_title = sanitize_filename(title)
            safe_title = truncate_filename_by_bytes(safe_title, max_bytes=200)

            output_path = os.path.join(OUTPUT_DIR, f"{safe_title}.mp4")

            concat_videos(intro_file, asset_file, output_path)

            print(f"   ✅ 输出: {safe_title}.mp4")

        print(f"\n✅ 所有资产视频生成完成!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    try:
        generate_asset_videos()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
