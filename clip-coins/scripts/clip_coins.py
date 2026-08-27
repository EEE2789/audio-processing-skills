#!/usr/bin/env python3
"""
基于 Video4 和资产时间轴，自动剪辑每个币种的独立视频

剪辑规则：
1. 开头介绍（从 assets_timeline.json 读取）
2. 该币种本身的独立内容
3. 无封面
4. 保留字幕（Video4 已烧录）
"""

import sys
import os
import subprocess
import re
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 配置
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"


def get_latest_video4():
    """获取最新的 Video4 文件"""
    import glob

    video4_pattern = os.path.join(OUTPUT_DIR, "4字幕*.mp4")
    video4_files = glob.glob(video4_pattern)

    if not video4_files:
        return None

    video4_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return video4_files[0]


def get_latest_srt():
    """获取最新的字幕文件"""
    import glob

    srt_pattern = os.path.join(SUBTITLE_DIR, "简体*.srt")
    srt_files = glob.glob(srt_pattern)

    if not srt_files:
        return None

    srt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return srt_files[0]


def get_timeline_json():
    """获取资产时间轴 JSON 文件（智能检查）

    Returns:
        timeline_path: JSON 文件路径
        或 None: 文件不存在或需要重新生成
    """
    timeline_path = os.path.join(SUBTITLE_DIR, "assets_timeline.json")

    if not os.path.exists(timeline_path):
        return None

    # 检查 JSON 文件的修改时间是否比最新字幕文件新
    latest_srt = get_latest_srt()
    if latest_srt:
        srt_mtime = os.path.getmtime(latest_srt)
        json_mtime = os.path.getmtime(timeline_path)

        # 如果字幕文件比 JSON 新，说明需要重新生成
        if srt_mtime > json_mtime:
            return None

    return timeline_path


def extract_clip(video_path, start_s, end_s, output_path):
    """提取视频片段"""
    if end_s <= start_s:
        raise ValueError(f"结束时间 {end_s} 必须大于开始时间 {start_s}")

    duration = end_s - start_s

    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-ss", f"{start_s:.3f}",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-crf", "15",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
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
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.2",
            "-crf", "15",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "320k",
            "-y", output_path
        ]

        subprocess.run(cmd, capture_output=True, check=True)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def clip_coin_video(video4_path, intro, assets, coin_index, output_dir, skip_intro=False):
    """剪辑单个币种视频

    Args:
        video4_path: Video4 文件路径
        intro: 开头介绍数据
        assets: 资产列表
        coin_index: 币种索引（在 assets 列表中的位置）
        output_dir: 输出目录
        skip_intro: 是否跳过开头介绍（默认 False）

    Returns:
        output_path: 输出文件路径
    """
    if coin_index >= len(assets):
        raise IndexError(f"币种索引 {coin_index} 超出范围（共 {len(assets)} 个币种）")

    coin = assets[coin_index]
    coin_name = coin['name']

    print(f"\n🎬 正在处理 {coin_name}...")

    # 时间转换（毫秒转秒）
    intro_start = intro['start_ms'] / 1000
    intro_end = intro['end_ms'] / 1000

    # 使用 JSON 中提供的时间范围
    coin_start = coin['start_ms'] / 1000
    coin_end = coin['end_ms'] / 1000

    # 计算时长
    duration_s = coin_end - coin_start
    if duration_s >= 60:
        duration_str = f"{duration_s/60:.1f}分钟"
    else:
        duration_str = f"{duration_s:.1f}秒"

    if skip_intro:
        print(f"   ⏭️  跳过开头介绍")
        print(f"   {coin_name}内容: {coin_start:.3f}s - {coin_end:.3f}s ({duration_str})")
    else:
        print(f"   开头介绍: {intro_start:.3f}s - {intro_end:.3f}s")
        print(f"   {coin_name}内容: {coin_start:.3f}s - {coin_end:.3f}s ({duration_str})")

    # 临时目录
    temp_dir = tempfile.mkdtemp()

    try:
        video_files_to_concat = []

        # 如果不跳过开头介绍，则提取开头介绍
        if not skip_intro:
            intro_file = os.path.join(temp_dir, "intro.mp4")
            extract_clip(video4_path, intro_start, intro_end, intro_file)
            print(f"   ✅ 开头介绍提取完成")
            video_files_to_concat.append(intro_file)

        # 提取币种内容
        content_file = os.path.join(temp_dir, "content.mp4")
        extract_clip(video4_path, coin_start, coin_end, content_file)
        print(f"   ✅ {coin_name}内容提取完成")
        video_files_to_concat.append(content_file)

        # 获取日期（从视频文件名）
        date_match = re.search(r'(\d{2})\.?(\d{2})', os.path.basename(video4_path))
        if date_match:
            month, day = date_match.groups()
            date_str = f"{month.zfill(2)}{day.zfill(2)}"
        else:
            date_str = datetime.now().strftime("%m%d")

        # 输出文件名
        output_filename = f"{date_str}{coin_name}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        # 拼接视频（如果有多个文件）
        if len(video_files_to_concat) > 1:
            concat_videos(video_files_to_concat, output_path)
            print(f"   ✅ 视频拼接完成")
        elif len(video_files_to_concat) == 1:
            # 只有一个文件，直接复制
            shutil.copy(video_files_to_concat[0], output_path)
            print(f"   ✅ 直接输出（无需拼接）")
        else:
            raise ValueError("没有可用的视频片段")

        print(f"   📁 输出文件: {output_path}")

        return output_path

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='基于 Video4 和资产时间轴剪辑币种视频')
    parser.add_argument('video4_path', nargs='?', help='Video4 文件路径（可选）')
    parser.add_argument('timeline_path', nargs='?', help='资产时间轴 JSON 文件路径（可选）')
    parser.add_argument('--skip-intro', action='store_true', help='跳过开头介绍（仅剪辑币种内容）')

    args = parser.parse_args()

    # 获取 Video4
    if args.video4_path:
        video4_path = args.video4_path
    else:
        video4_path = get_latest_video4()
        if not video4_path:
            print("❌ 未找到 Video4")
            print("   请先运行 video4-processing skill 生成 Video4")
            sys.exit(1)

    print(f"📂 Video4: {video4_path}")

    # 获取资产时间轴
    if args.timeline_path:
        timeline_path = args.timeline_path
    else:
        timeline_path = get_timeline_json()
        if not timeline_path:
            print("❌ 未找到资产时间轴文件或文件已过期")
            print("   请先运行 analyze-assets skill 生成 assets_timeline.json：")
            print("   python3 /Users/ai/.claude/skills/analyze-assets/scripts/analyze_assets.py")
            sys.exit(1)

    print(f"📄 资产时间轴: {timeline_path}")

    # 读取时间轴数据
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)

    print(f"📅 日期: {timeline_data['date']}")

    # 兼容旧版和新版 JSON 格式
    total_count = timeline_data.get('total_count') or timeline_data.get('total_segments', 0)
    print(f"👥 总资产数: {total_count}")

    intro = timeline_data['intro']
    # 兼容旧版 assets 和新版 segments
    assets = timeline_data.get('assets') or timeline_data.get('segments', [])

    print(f"\n📋 开头介绍时间: {intro['start_time']} - {intro['end_time']}")
    print(f"\n📋 资产列表:")
    for i, asset in enumerate(assets):
        print(f"   {i + 1}. {asset['name']} - {asset['start_time']}")

    # 剪辑每个币种（跳过比特币）
    print("\n" + "=" * 80)
    print("开始剪辑...")
    print("=" * 80)

    output_files = []
    failed_files = []

    for i, asset in enumerate(assets):
        coin_name = asset['name']

        # 跳过比特币
        if coin_name == '比特币':
            print(f"\n⏭️  跳过比特币（主视频内容）")
            continue

        try:
            output_path = clip_coin_video(video4_path, intro, assets, i, OUTPUT_DIR, skip_intro=args.skip_intro)
            output_files.append((coin_name, output_path))
        except Exception as e:
            print(f"\n❌ 剪辑 {coin_name} 失败: {e}")
            failed_files.append((coin_name, str(e)))
            continue

    # 总结
    print("\n" + "=" * 80)
    if failed_files:
        print(f"❌ 剪辑完成，但有 {len(failed_files)} 个失败")
        print("=" * 80)
    else:
        print("✅ 剪辑完成！")
        print("=" * 80)

    print(f"\n📊 剪辑统计:")
    print(f"   总资产数: {len(assets)}")
    print(f"   跳过: 1（比特币）")
    print(f"   成功剪辑: {len(output_files)}")
    print(f"   失败: {len(failed_files)}")

    if failed_files:
        print(f"\n❌ 失败详情:")
        for coin_name, error in failed_files:
            print(f"   {coin_name}: {error}")

    print(f"\n📁 输出文件:")
    for coin_name, file_path in output_files:
        print(f"   {coin_name}: {file_path}")

    # 如果有失败，以非零状态退出
    if failed_files:
        print(f"\n⚠️  由于 {len(failed_files)} 个币种剪辑失败，程序以错误状态退出")
        sys.exit(1)


if __name__ == "__main__":
    main()
