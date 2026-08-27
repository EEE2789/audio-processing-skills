#!/usr/bin/env python3
"""
以太坊视频剪辑工具

从币圈行情视频中提取以太坊相关内容片段，拼接成独立的以太坊视频。
"""

import sys
import os
import subprocess
import re
import tempfile
import shutil
import json
from datetime import datetime
from pathlib import Path

# ====== 配置 ======
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
INPUT_DIR = "/Users/ai/Documents/video_pipeline/1input"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"

# 编码参数
VIDEO_CODEC = "libx264"
PIXEL_FMT = "yuv420p"
PROFILE = "high"
LEVEL = "4.2"
CRF = "15"
PRESET = "veryfast"
FPS = "29.97"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "320k"


def get_video4_or_latest():
    """获取 Video4（优先）或原始视频"""
    import glob

    # 首先查找 Video4
    video4_pattern = os.path.join(OUTPUT_DIR, "4字幕*.mp4")
    video4_files = glob.glob(video4_pattern)

    if video4_files:
        # 按修改时间排序，取最新的
        video4_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return video4_files[0], "video4"

    # Video4 不存在，查找原始视频
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']
    video_files = []
    for file in os.listdir(INPUT_DIR):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            file_path = os.path.join(INPUT_DIR, file)
            video_files.append((file_path, os.path.getmtime(file_path)))

    if not video_files:
        raise RuntimeError(f"❌ 在 {INPUT_DIR} 中未找到视频文件")

    video_files.sort(key=lambda x: x[1], reverse=True)
    return video_files[0][0], "original"


def get_latest_subtitle():
    """获取 3daily 中最新的简体字幕"""
    srt_files = []
    for file in os.listdir(SUBTITLE_DIR):
        if file.startswith('简体') and file.endswith('.srt'):
            file_path = os.path.join(SUBTITLE_DIR, file)
            srt_files.append((file_path, os.path.getmtime(file_path)))

    if not srt_files:
        raise RuntimeError(f"❌ 在 {SUBTITLE_DIR} 中未找到简体字幕")

    srt_files.sort(key=lambda x: x[1], reverse=True)
    return srt_files[0][0]


def parse_srt(srt_path):
    """解析 SRT 字幕文件

    返回: [(start_ms, end_ms, text), ...]
    """
    time_re = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")

    def to_ms(h, m, s, ms):
        return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    subtitles = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            parts = time_line.split(' --> ')
            if len(parts) == 2:
                ma = time_re.match(parts[0])
                mb = time_re.match(parts[1])
                if ma and mb:
                    start = to_ms(*ma.groups())
                    end = to_ms(*mb.groups())
                    text = '\n'.join(lines[2:])
                    subtitles.append((start, end, text))

    return subtitles


def find_ethereum_start(subtitles, skip_first_ms=0):
    """找到以太坊内容开始的时间点

    逻辑：
    1. 优先查找明确的过渡短语（如"那以太坊"、"我们看一下以太坊"）
    2. 如果没找到，查找包含过渡词+以太坊的组合（如"接下来...以太坊"、"我们再看...以太坊"）
    3. 只有在明确表达"接下来要看以太坊"的语义时，才记录开始时间
    """
    # 优先级明确的过渡短语
    priority_keywords = [
        '那以太坊',           # "比特币讲完了，那以太坊..." - 最通用
        '我们看一下以太坊',  # "我们看一下以太坊" - 常见
        '那说一下以太坊',     # "那说一下以太坊" - 常见
        '我们再看以太坊',     # "我们再看以太坊" - 常见
        '接下来以太坊',       # "接下来以太坊" - 常见
        '再看一下以太坊',     # "再看一下以太坊" - 常见
        '我们来看以太坊',     # "我们来看以太坊" - 常见
    ]

    for start, end, text in subtitles:
        if start < skip_first_ms:
            continue
        for kw in priority_keywords:
            if kw in text:
                print(f"   ✅ 找到明确过渡语 '{kw}' 在 {start/1000:.2f}s")
                return start

    # 兜底：查找包含过渡词 + 以太坊的组合
    # 要求：以太坊前面必须有过渡词，表明"接下来要看"的语义
    transition_words = ['我们', '那', '再看', '接下来', '然后']
    eth_keywords = ['以太坊', '以太']

    for start, end, text in subtitles:
        if start < skip_first_ms:
            continue

        # 检查是否同时包含过渡词和以太坊关键词
        has_transition = any(tw in text for tw in transition_words)
        has_eth = any(ek in text for ek in eth_keywords)

        if has_transition and has_eth:
            print(f"   ✅ 找到过渡+以太坊组合 在 {start/1000:.2f}s: \"{text[:30]}...\"")
            return start

    print(f"   ⚠️  未找到明确的以太坊过渡语，使用视频最后 60 秒")
    return None


def get_assets_timeline():
    """读取资产时间轴文件"""
    timeline_path = os.path.join(SUBTITLE_DIR, "assets_timeline.json")
    if not os.path.exists(timeline_path):
        return None

    with open(timeline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_ethereum_times(timeline_data):
    """从资产时间轴获取以太坊开始和结束时间"""
    if timeline_data is None:
        return None, None

    # 支持 'assets' 和 'segments' 两种键名
    assets_list = timeline_data.get('assets') or timeline_data.get('segments') or []
    for asset in assets_list:
        if asset.get('name') == '以太坊':
            return asset.get('start_ms'), asset.get('end_ms')

    return None, None


def find_intro_end(subtitles):
    """找到"我是军长"结束的时间点"""
    for start, end, text in subtitles:
        if '我是军长' in text or '军长' in text:
            return end
    # 默认前4秒
    return 4500


def add_cover_only(video_path, cover_path, output_path):
    """添加封面（不烧录字幕，因为 Video4 已有字幕）"""
    # 获取视频属性
    cmd = [FFMPEG_PATH, "-i", video_path, "-hide_banner"]
    result = subprocess.run(cmd, capture_output=True)
    output = result.stderr.decode('utf-8')

    width, height, fps = 2100, 1080, "2997/100"
    for line in output.split('\n'):
        if 'Stream #0:0' in line and 'Video' in line:
            match = re.search(r'(\d{3,4})x(\d{3,4})', line)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
            match = re.search(r'(\d+)/(\d+)\s+fps', line)
            if match:
                fps = f"{match.group(1)}/{match.group(2)}"
            break

    # 拼接封面（0.2秒）+ 视频内容
    filter_complex = (
        f"[0:v]scale={width}:{height},setsar=1:1,fps={fps},format=yuv420p[vcover];"
        f"[1:v]scale={width}:{height},setsar=1:1,fps={fps},format=yuv420p[vmain];"
        f"[vcover][vmain]concat=n=2:v=1:a=0[vout]"
    )

    cmd = [
        FFMPEG_PATH,
        "-loop", "1", "-t", "0.2", "-i", cover_path,
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", VIDEO_CODEC,
        "-profile:v", PROFILE,
        "-level", LEVEL,
        "-crf", CRF,
        "-preset", PRESET,
        "-pix_fmt", PIXEL_FMT,
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"❌ 封面拼接失败: {result.stderr.decode('utf-8')}")


def sanitize_filename(filename):
    """清理文件名，只移除真正不合法的字符"""
    invalid_chars = ['<', '>', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename


def truncate_filename_by_bytes(filename, max_bytes=250):
    """按字节长度截断文件名（保留扩展名）"""
    # 编码为字节
    filename_bytes = filename.encode('utf-8')

    if len(filename_bytes) <= max_bytes:
        return filename

    # 截断到指定字节数
    truncated = filename_bytes[:max_bytes].decode('utf-8', errors='ignore')
    return truncated


def generate_ethereum_video(cover_path, video_title):
    """生成以太坊视频

    Args:
        cover_path: 封面图片路径
        video_title: 视频标题（60-80字）
    """
    print(f"\n📝 正在生成以太坊视频...")

    # 检查 Video4 是否存在
    video4_path, video_type = get_video4_or_latest()

    if video_type == "video4":
        print(f"✅ 找到 Video4: {video4_path}")
    else:
        print(f"⚠️  未找到 Video4，使用原始视频: {video4_path}")
        print(f"💡 提示：建议先生成 Video4（使用 video4-processing skill）")

    # 读取字幕
    srt_path = get_latest_subtitle()
    print(f"✅ 找到字幕: {srt_path}")

    subtitles = parse_srt(srt_path)

    # 读取资产时间轴
    timeline_data = get_assets_timeline()
    eth_start_ms, eth_end_ms = get_ethereum_times(timeline_data)

    # 获取视频总时长（用于兜底逻辑）
    cmd = [FFMPEG_PATH, "-i", video4_path, "-hide_banner"]
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

    if duration_ms is None:
        raise RuntimeError("❌ 无法获取视频时长")

    # 优先使用资产时间轴中的时间范围
    if eth_start_ms is not None and eth_end_ms is not None:
        print(f"   ✅ 使用资产时间轴时间范围: {eth_start_ms/1000:.2f}s - {eth_end_ms/1000:.2f}s")
    else:
        # 兜底：使用关键词搜索
        print(f"   ⚠️ 未找到资产时间轴，使用关键词搜索")
        if eth_end_ms is None:
            eth_end_ms = duration_ms
        if eth_start_ms is None:
            eth_start_ms = find_ethereum_start(subtitles)
            if eth_start_ms is None:
                eth_start_ms = max(0, duration_ms - 60000)
        print(f"   📍 以太坊内容: {eth_start_ms/1000:.2f}s - {eth_end_ms/1000:.2f}s")

    # 找到"我是军长"结束时间
    # 找到"我是军长"结束时间
    intro_end_ms = find_intro_end(subtitles)

    # 提取视频片段
    print(f"\n📌 正在提取视频片段...")

    temp_dir = tempfile.mkdtemp()

    try:
        # 提取开头介绍（重新编码以确保视频流完整）
        intro_file = os.path.join(temp_dir, "intro.mp4")
        cmd = [
            FFMPEG_PATH, "-i", video4_path,
            "-ss", "0",
            "-t", f"{intro_end_ms / 1000:.3f}",
            "-c:v", VIDEO_CODEC,
            "-profile:v", PROFILE,
            "-level", LEVEL,
            "-crf", CRF,
            "-preset", PRESET,
            "-pix_fmt", PIXEL_FMT,
            "-c:a", "copy",
            "-y", intro_file
        ]
        subprocess.run(cmd, capture_output=True)

        # 提取以太坊内容（重新编码以确保视频流完整）
        eth_file = os.path.join(temp_dir, "ethereum.mp4")
        cmd = [
            FFMPEG_PATH, "-i", video4_path,
            "-ss", f"{eth_start_ms / 1000:.3f}",
            "-t", f"{(eth_end_ms - eth_start_ms) / 1000:.3f}",
            "-c:v", VIDEO_CODEC,
            "-profile:v", PROFILE,
            "-level", LEVEL,
            "-crf", CRF,
            "-preset", PRESET,
            "-pix_fmt", PIXEL_FMT,
            "-c:a", "copy",
            "-y", eth_file
        ]
        subprocess.run(cmd, capture_output=True)

        # 拼接开头介绍 + 以太坊内容
        content_file = os.path.join(temp_dir, "content.mp4")

        # 创建 concat 文件
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            f.write(f"file '{intro_file}'\n")
            f.write(f"file '{eth_file}'\n")

        cmd = [
            FFMPEG_PATH, "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", VIDEO_CODEC,
            "-profile:v", PROFILE,
            "-level", LEVEL,
            "-crf", CRF,
            "-preset", PRESET,
            "-pix_fmt", PIXEL_FMT,
            "-c:a", "copy",
            "-y", content_file
        ]
        subprocess.run(cmd, capture_output=True)

        # 添加封面
        today = datetime.now()
        month_day = today.strftime("%m.%d")

        # 去除视频标题末尾的标点符号
        if video_title.endswith('。'):
            video_title = video_title[:-1]

        # 构建完整标题
        full_title = f"{month_day}以太坊价格今日行情：{video_title}（以太坊合约交易）军长"

        # 清理文件名
        safe_title = sanitize_filename(full_title)
        safe_title = truncate_filename_by_bytes(safe_title, max_bytes=200)

        output_path = os.path.join(OUTPUT_DIR, f"{safe_title}.mp4")

        print(f"\n📌 正在添加封面...")

        add_cover_only(content_file, cover_path, output_path)

        print(f"\n✅ 以太坊视频生成成功!")
        print(f"📁 输出文件: {output_path}")
        print(f"\n📋 视频标题: {safe_title}.mp4")
        print(f"📌 完整标题: {full_title}")

        print(f"\n📊 时间信息:")
        print(f"   - 开头介绍: 0s - {intro_end_ms / 1000:.2f}s")
        print(f"   - 以太坊片段: {eth_start_ms / 1000:.2f}s - {eth_end_ms / 1000:.2f}s")
        print(f"   - 跳过的比特币内容: {intro_end_ms / 1000:.2f}s - {eth_start_ms / 1000:.2f}s ({(eth_start_ms - intro_end_ms) / 1000:.1f}秒)")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='生成以太坊视频')
    parser.add_argument('--cover-path', type=str, required=True, help='封面图片路径')
    parser.add_argument('--video-title', type=str, required=True, help='视频标题（60-80字）')

    args = parser.parse_args()

    try:
        generate_ethereum_video(args.cover_path, args.video_title)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
