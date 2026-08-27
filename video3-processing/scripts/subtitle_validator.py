#!/usr/bin/env python3
"""
字幕验证器 - 验证字幕时间轴正确性
"""

import subprocess
import json
from pathlib import Path


def get_audio_duration(audio_file):
    """获取音频时长"""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_file)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def parse_srt_time(time_str):
    """解析 SRT 时间字符串为秒数"""
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def validate_subtitle(subtitle_file, reference_audio=None, reference_volc=None):
    """
    验证字幕时间轴正确性
    """
    
    issues = []
    
    # 读取字幕文件
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = [b for b in content.split('\n\n') if '-->' in b]
    
    if not blocks:
        issues.append("❌ 字幕文件为空")
        return issues
    
    # 提取时间信息
    first_line = blocks[0].split('\n')
    first_time_range = first_line[1].strip()
    last_line = blocks[-1].split('\n')
    last_time_range = last_line[1].strip()
    
    first_start = parse_srt_time(first_time_range.split(' --> ')[0])
    last_end = parse_srt_time(last_time_range.split(' --> ')[1])
    subtitle_count = len(blocks)
    
    print(f"📋 字幕文件: {subtitle_file}")
    print(f"   条数: {subtitle_count}")
    print(f"   时间范围: {first_time_range} --> {last_time_range}")
    
    # 验证 1: 检查参考音频
    if reference_audio:
        audio_duration = get_audio_duration(reference_audio)
        print(f"\n🎵 参考音频: {reference_audio}")
        print(f"   时长: {audio_duration:.3f}秒")
        
        if last_end > audio_duration + 2:
            issues.append(f"⚠️ 字幕超出音频过多: {last_end:.3f}s > {audio_duration:.3f}s (差异 {last_end - audio_duration:.3f}s)")
        elif last_end < audio_duration - 5:
            issues.append(f"⚠️ 字幕覆盖不足: {last_end:.3f}s < {audio_duration:.3f}s (差异 {audio_duration - last_end:.3f}s)")
        else:
            print(f"   ✅ 字幕与音频时长匹配")
    
    # 验证 2: 检查火山引擎参考
    expected_count = None
    if reference_volc:
        with open(reference_volc, 'r') as f:
            volc_data = json.load(f)
        expected_count = len(volc_data.get('utterances', []))
        
        print(f"\n🔥 火山引擎参考: {reference_volc}")
        print(f"   语段数: {expected_count}")
        
        if subtitle_count != expected_count:
            issues.append(f"⚠️ 字幕条数不匹配: {subtitle_count} ≠ {expected_count} (差异 {abs(subtitle_count - expected_count)} 条)")
        else:
            print(f"   ✅ 字幕条数匹配")
    
    # 验证 3: 检查字幕开始时间
    print(f"\n⏰ 时间分析:")
    print(f"   第一条开始: {first_start:.3f}秒")
    print(f"   最后条结束: {last_end:.3f}秒")
    print(f"   总覆盖时长: {last_end - first_start:.3f}秒")
    
    if first_start > 5:
        issues.append(f"⚠️ 字幕开始过晚: {first_start:.3f}秒 (可能需要偏移)")
    elif first_start < 0:
        issues.append(f"❌ 字幕开始时间为负")
    else:
        print(f"   ✅ 字幕开始时间正常")
    
    # 总结
    print(f"\n{'='*50}")
    if not issues:
        print("✅ 字幕验证通过")
    else:
        print("❌ 字幕验证失败，发现以下问题:")
        for issue in issues:
            print(f"   {issue}")
    
    return issues


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python subtitle_validator.py <字幕.srt> [参考音频.wav] [火山引擎.json]")
        sys.exit(1)
    
    subtitle_file = sys.argv[1]
    audio_file = sys.argv[2] if len(sys.argv) > 2 else None
    volc_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    issues = validate_subtitle(subtitle_file, audio_file, volc_file)
    
    sys.exit(0 if not issues else 1)
