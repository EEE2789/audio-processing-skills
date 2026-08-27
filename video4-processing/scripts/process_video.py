#!/usr/bin/env python3
"""
Video4 剪辑用｜行情视频 1.1倍速 + 字幕（无封面）

基于原始视频生成 Video4，作为所有后续视频剪辑的统一源。
无封面，字幕不延后。

输入：/Users/ai/Documents/video_pipeline/1input/ 中的视频文件 + 简体字幕
输出：/Users/ai/Documents/video_pipeline/2output/4字幕_MMDD.mp4
"""

import sys
import os
import subprocess
import re
import tempfile
import shutil
from datetime import datetime

# ====== 固定配置 ======
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
INPUT_DIR = "/Users/ai/Documents/video_pipeline/1input"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"

# 编码参数（固定）
VIDEO_CODEC = "libx264"
PIXEL_FMT = "yuv420p"
PROFILE = "high"
LEVEL = "4.2"
CRF = "15"
PRESET = "veryfast"
FPS = "29.97"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "320k"


def validate_ffmpeg():
    """校验 ffmpeg 是否存在"""
    if not os.path.exists(FFMPEG_PATH):
        raise RuntimeError(f"❌ ffmpeg 不存在于指定路径: {FFMPEG_PATH}")


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


def get_latest_subtitle():
    """自动获取 3daily 文件夹中最新的简体字幕"""
    if not os.path.exists(SUBTITLE_DIR):
        raise RuntimeError(f"❌ 字幕目录不存在: {SUBTITLE_DIR}")

    # 查找简体字幕
    srt_files = []
    for file in os.listdir(SUBTITLE_DIR):
        if file.startswith('简体') and file.endswith('.srt'):
            file_path = os.path.join(SUBTITLE_DIR, file)
            srt_files.append((file_path, os.path.getmtime(file_path)))

    if not srt_files:
        raise RuntimeError(f"❌ 在 {SUBTITLE_DIR} 中未找到简体字幕 (简体*.srt)")

    # 按修改时间排序，获取最新的
    srt_files.sort(key=lambda x: x[1], reverse=True)
    latest_srt = srt_files[0][0]

    print(f"📂 自动找到最新字幕: {os.path.basename(latest_srt)}")
    return latest_srt


def get_video_properties(video_path):
    """获取视频属性（分辨率、帧率）"""
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-hide_banner"
    ]
    result = subprocess.run(cmd, capture_output=True)
    output = result.stderr.decode('utf-8')

    width = None
    height = None
    fps = "2997/100"  # 默认 29.97 fps

    for line in output.split('\n'):
        if 'Stream #0:0' in line and 'Video' in line:
            # 解析分辨率
            match = re.search(r'(\d{3,4})x(\d{3,4})', line)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
            # 解析帧率
            match = re.search(r'(\d+)/(\d+)\s+fps', line)
            if match:
                fps = f"{match.group(1)}/{match.group(2)}"

    return width, height, fps


def escape_subtitle_path(path):
    """转义字幕路径用于 ffmpeg subtitles 滤镜"""
    path = path.replace('\\', '\\\\\\\\')  # \\  -> \\\
    path = path.replace(':', '\\\\:')    # :  -> \:
    path = path.replace("'", "\\'")    # '  -> \\'"
    return path


def process_video(input_video, subtitle_path):
    """
    处理视频：1.1倍速 + 轻微去重 + 字幕烧录

    处理规则：
    1. 播放速度：1.1倍（音画同步，不改变音调）
    2. 去重：轻微裁剪 + 锐化
    3. 字幕：简体烧录（与 Video3 格式一致）
    4. 字幕时间轴：不延后（与原视频一致）
    5. 无封面
    6. 编码：libx264 / yuv420p / high / 4.2 / CRF 15
    7. 音频：AAC 320k
    """
    # 生成输出文件名
    now = datetime.now()
    month_day = now.strftime("%m.%d")
    output_filename = f"4字幕{month_day}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 获取视频属性
    width, height, fps = get_video_properties(input_video)
    print(f"📐 视频属性: {width}x{height} @ {fps} fps")

    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    try:
        temp_srt = os.path.join(temp_dir, "subtitle.srt")
        shutil.copy(subtitle_path, temp_srt)

        # 转义字幕路径
        srt_escaped = escape_subtitle_path(temp_srt)
        fontdir = "/System/Library/Fonts"

        # 字幕样式（与 Video3 完全一致）
        # PrimaryColour=&H00FFFFFF&: 白色文字，完全不透明
        # BackColour=&H80808080&: 灰色背景，50% 透明度
        # BorderStyle=1: 方框背景 + 描边
        # Outline=0: 无描边
        # OutlineColour=&H00000000&: 描边颜色设为透明黑色
        subtitle_filter = (
            f"subtitles='{srt_escaped}':fontsdir='{fontdir}':"
            "force_style='FontName=PingFangSC-Medium,FontSize=22,"
            "PrimaryColour=&H00FFFFFF&,BackColour=&H80808080&,"
            "OutlineColour=&H00000000&,BorderStyle=1,Outline=0,Shadow=0,MarginV=30,Alignment=2'"
        )

        # 1.1倍速 + 轻微去重 + 字幕烧录
        filter_complex = (
            f"[0:v]setpts=0.909*PTS,crop=iw*0.99:ih*0.99:(iw-iw*0.99)/2:(ih-ih*0.99)/2,setsar=1:1,fps={fps},format=yuv420p,{subtitle_filter}[vout];"
            "[0:a]atempo=1.1[aout]"
        )

        cmd = [
            FFMPEG_PATH,
            "-i", input_video,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", VIDEO_CODEC,
            "-profile:v", PROFILE,
            "-level", LEVEL,
            "-crf", CRF,
            "-preset", PRESET,
            "-pix_fmt", PIXEL_FMT,
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-y",
            output_path
        ]

        print(f"🎬 正在处理视频...")
        print(f"📝 输入: {input_video}")
        print(f"📝 字幕: {subtitle_path}")
        print(f"📝 输出: {output_path}")
        print(f"⚙️  参数: 1.1倍速 | {FPS} fps | CRF {CRF} | {PRESET} | 字幕烧录 | 无封面")

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else result.stdout.decode('utf-8')
            raise RuntimeError(f"❌ ffmpeg 执行失败:\n{error_msg}")

    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 验证输出文件
    if not os.path.exists(output_path):
        raise RuntimeError(f"❌ 输出文件未生成: {output_path}")

    return output_path


def main():
    try:
        # 1. 校验 ffmpeg
        validate_ffmpeg()

        # 2. 解析参数或自动获取
        if len(sys.argv) >= 2:
            video_path = sys.argv[1]
            print(f"📂 使用指定视频: {video_path}")
        else:
            video_path = get_latest_video()

        if len(sys.argv) >= 3:
            subtitle_path = sys.argv[2]
            print(f"📂 使用指定字幕: {subtitle_path}")
        else:
            subtitle_path = get_latest_subtitle()

        # 3. 字幕验证（Video4 生成前强制检查）
        print("\n" + "="*50)
        print("🔍 Video4 生成前字幕验证")
        print("="*50)
        
        try:
            from subtitle_validator import validate_subtitle
            from backup_manager import create_backup
            
            # 创建当前字幕备份
            with open(subtitle_path, 'r') as f:
                sub_content = f.read()
            sub_count = len([b for b in sub_content.split('\n\n') if '-->' in b])
            create_backup(subtitle_path, sub_count, "Video4生成前", "自动备份")
            
            # 验证字幕（Video4 无封面，字幕不延后）
            audio_path = subtitle_path.replace("/Users/ai/Documents/video_pipeline/3daily/简体", "/Users/ai/Documents/video_pipeline/3daily/audio/").replace(".srt", ".wav")
            volc_path = "/Users/ai/.claude/skills/jz字幕/volcengine_result.json"
            
            print("ℹ️  Video4 说明: 无封面，字幕不延后")
            issues = validate_subtitle(subtitle_path, audio_path if os.path.exists(audio_path) else None, volc_path if os.path.exists(volc_path) else None)
            
            if issues:
                print("\n⚠️ 字幕验证发现问题，建议检查后再生成")
        except ImportError as e:
            print(f"⚠️ 无法导入验证器: {e}")
        
        # 4. 处理视频
        output_path = process_video(video_path, subtitle_path)

        # 5. 返回结果
        print(f"\n✅ Video4 生成成功: {output_path}")
        print(f"📁 文件位置: {OUTPUT_DIR}")

    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
