#!/usr/bin/env python3
"""
时间轴分析器 - 标准化视频/音频时间轴差异分析
"""

import subprocess
import sys


def get_media_duration(media_file):
    """获取媒体文件时长"""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(media_file)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def analyze_timing_difference(video_file, audio_file, audio_speed=1.1):
    """
    标准化时间轴差异分析
    
    Args:
        video_file: 视频文件路径
        audio_file: 音频文件路径
        audio_speed: 音频加速倍数（默认 1.1）
    
    Returns:
        dict: 分析结果
    """
    
    print("="*60)
    print("📊 时间轴分析（标准化）")
    print("="*60)
    
    # 获取时长
    video_duration = get_media_duration(video_file)
    audio_duration = get_media_duration(audio_file)
    
    # 计算原速音频时长
    original_audio_duration = audio_duration * audio_speed
    
    # 计算差异
    difference = video_duration - original_audio_duration
    
    # 输出分析
    print(f"\n原始数据:")
    print(f"  原视频时长: {video_duration:.3f} 秒 ({video_duration/60:.2f} 分钟)")
    print(f"  音频时长 ({audio_speed}x): {audio_duration:.3f} 秒 ({audio_duration/60:.2f} 分钟)")
    
    print(f"\n换算后:")
    print(f"  原音频时长 (1.0x): {original_audio_duration:.3f} 秒 ({original_audio_duration/60:.2f} 分钟)")
    
    print(f"\n差异分析:")
    print(f"  差异: {difference:+.3f} 秒 ({difference/60:+.2f} 分钟)")
    print(f"  相对差异: {abs(difference)/video_duration*100:.1f}%")
    
    # 判断和建议
    print(f"\n分析结果:")
    
    offset = 0
    status = "正常"
    
    if abs(difference) < 1:
        print(f"  ✅ {status}: 视频/音频时长基本一致，无需偏移")
        offset = 0
    elif abs(difference) < 5:
        print(f"  ⚠️ 小幅差异: 可能是开头/结尾静音，建议手动检查")
        offset = 0
        status = "需确认"
    elif difference > 10:
        print(f"  ❌ 视频过长: 视频比音频长 {difference:.1f} 秒")
        print(f"     建议: 检查视频开头是否有片头，或裁剪开头")
        offset = difference / audio_speed  # 转换到加速后的偏移量
        status = "视频过长"
    elif difference < -10:
        print(f"  ❌ 视频过短: 视频比音频短 {abs(difference):.1f} 秒")
        print(f"     建议: 检查音频是否完整，或视频是否被裁剪")
        offset = 0
        status = "视频过短"
    
    # 字幕偏移建议
    if offset > 0:
        print(f"\n字幕偏移建议:")
        print(f"  如果字幕基于音频生成，需要向后偏移: {offset:.3f} 秒")
        print(f"  偏移公式: 新时间 = 原时间 + {offset:.3f} 秒")
    
    return {
        'video_duration': video_duration,
        'audio_duration': audio_duration,
        'original_audio_duration': original_audio_duration,
        'difference': difference,
        'offset': offset,
        'status': status
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python timing_analyzer.py <视频.mp4> <音频.wav> [音频倍速，默认1.1]")
        print("\n示例:")
        print("  python timing_analyzer.py video.mp4 audio.wav")
        print("  python timing_analyzer.py video.mp4 audio.wav 1.1")
        sys.exit(1)
    
    video_file = sys.argv[1]
    audio_file = sys.argv[2]
    audio_speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
    
    result = analyze_timing_difference(video_file, audio_file, audio_speed)
    
    print(f"\n结论: {result['status']}")
    if result['offset'] > 0:
        print(f"建议偏移: {result['offset']:.3f} 秒")


if __name__ == '__main__':
    main()
