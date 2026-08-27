#!/usr/bin/env python3
"""
从视频提取音频并加速到 1.1 倍

使用方法:
    python scripts/extract_audio.py <video_path>

输出:
    /Users/ai/Documents/video_pipeline/3daily/audio/<原文件名>_YYYYMMDD.wav
"""

import sys
import os
import subprocess
from datetime import datetime

# 固定配置
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/3daily/audio"
INPUT_DIR = "/Users/ai/Documents/video_pipeline/1input"

def validate_ffmpeg():
    """校验 ffmpeg 是否存在"""
    if not os.path.exists(FFMPEG_PATH):
        raise RuntimeError(f"❌ ffmpeg 不存在于指定路径: {FFMPEG_PATH}")

def validate_video(video_path):
    """校验视频文件"""
    if not os.path.exists(video_path):
        raise RuntimeError(f"❌ 视频文件不存在: {video_path}")
    if not os.access(video_path, os.R_OK):
        raise RuntimeError(f"❌ 视频文件不可读: {video_path}")
    check_audio_track(video_path)

def check_audio_track(video_path):
    """检查视频中的音轨"""
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-hide_banner"
    ]
    result = subprocess.run(cmd, capture_output=True, check=False)

    # 检查是否有音频流（ffmpeg 输出到 stderr）
    output = result.stderr.decode('utf-8')
    if "Audio" not in output:
        raise RuntimeError("❌ 视频中无音轨 (no audio stream)")

    return True

def get_latest_video():
    """自动获取 1input 文件夹中最新的视频文件"""
    if not os.path.exists(INPUT_DIR):
        raise RuntimeError(f"❌ 输入目录不存在: {INPUT_DIR}")

    # 支持的视频格式
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']

    # 获取所有视频文件
    video_files = []
    for file in os.listdir(INPUT_DIR):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            file_path = os.path.join(INPUT_DIR, file)
            video_files.append((file_path, os.path.getmtime(file_path)))

    if not video_files:
        raise RuntimeError(f"❌ 在 {INPUT_DIR} 中未找到视频文件")

    # 按修改时间排序，获取最新的
    video_files.sort(key=lambda x: x[1], reverse=True)
    latest_video = video_files[0][0]

    print(f"📂 自动找到最新视频: {os.path.basename(latest_video)}")

    return latest_video

def extract_and_accelerate_audio(video_path):
    """
    从视频提取音频并加速到 1.1 倍

    步骤:
    1. 提取音频
    2. 1.1 倍加速（保持音调）
    3. 转换为 16k/mono/pcm_s16le WAV
    """
    # 获取原文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # 生成输出文件名: 原文件名_YYYYMMDD.wav
    date_suffix = datetime.now().strftime("%Y%m%d")
    output_filename = f"{base_name}_{date_suffix}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 使用 ffmpeg 一步完成: 提取音频 + 1.1倍加速 + 格式转换
    # atempo=1.1: 1.1倍加速（保持音调）
    # -ar 16000: 采样率 16kHz
    # -ac 1: 单声道
    # -acodec pcm_s16le: 16位 PCM 编码
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-filter:a", "atempo=1.1",
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-y",  # 覆盖已存在的文件
        output_path
    ]

    print(f"🎬 正在处理: {video_path}")
    print(f"📝 输出: {output_path}")

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode != 0:
        error_msg = result.stderr.decode('utf-8') if result.stderr else result.stdout.decode('utf-8')
        raise RuntimeError(f"❌ ffmpeg 执行失败:\n{error_msg}")

    # 验证输出文件
    if not os.path.exists(output_path):
        raise RuntimeError(f"❌ 输出文件未生成: {output_path}")

    return output_path

def main():
    try:
        # 1. 校验 ffmpeg
        validate_ffmpeg()

        # 2. 自动获取最新视频（如果命令行指定了路径则使用指定路径）
        if len(sys.argv) >= 2:
            video_path = sys.argv[1]
            print(f"📂 使用指定视频: {video_path}")
        else:
            video_path = get_latest_video()

        # 3. 校验视频
        validate_video(video_path)

        # 4. 处理
        audio_path = extract_and_accelerate_audio(video_path)

        # 5. 返回结果
        print(f"✅ 音频生成成功: {audio_path}")
        print(audio_path)

    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
