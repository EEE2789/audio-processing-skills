#!/usr/bin/env python3
"""
字幕生成器 - 改进版
直接按顺序匹配火山引擎转录和用户审核稿
"""

import json
from datetime import timedelta
from pathlib import Path


def format_srt_time(seconds):
    """格式化 SRT 时间戳"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def generate_subtitle(volc_result_path, draft_file_path, output_path):
    """
    生成字幕文件
    
    Args:
        volc_result_path: 火山引擎转录结果 JSON 文件
        draft_file_path: 用户审核稿 TXT 文件
        output_path: 输出 SRT 文件路径
    """
    
    # 读取火山引擎结果
    with open(volc_result_path, 'r', encoding='utf-8') as f:
        volc_data = json.load(f)
    
    volc_utterances = volc_data.get('utterances', [])
    
    # 读取用户审核稿
    with open(draft_file_path, 'r', encoding='utf-8') as f:
        draft_lines = [line.strip() for line in f if line.strip()]
    
    # 验证条数
    if len(volc_utterances) != len(draft_lines):
        print(f"⚠️ 警告：火山引擎语段数({len(volc_utterances)}) 与审核稿行数({len(draft_lines)}) 不匹配")
        print(f"   将按最小条数生成：{min(len(volc_utterances), len(draft_lines))} 条")
    
    # 直接按顺序匹配
    subtitles = []
    count = min(len(volc_utterances), len(draft_lines))
    
    for i in range(count):
        volc = volc_utterances[i]
        draft_text = draft_lines[i]
        
        start_time = volc['start_time'] / 1000
        end_time = volc['end_time'] / 1000
        
        subtitles.append({
            'index': i + 1,
            'start': format_srt_time(start_time),
            'end': format_srt_time(end_time),
            'text': draft_text
        })
    
    # 生成 SRT 内容
    srt_content = ""
    for sub in subtitles:
        srt_content += f"{sub['index']}\n"
        srt_content += f"{sub['start']} --> {sub['end']}\n"
        srt_content += f"{sub['text']}\n\n"
    
    # 写入文件
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    print(f"✅ 字幕生成完成: {output_path}")
    print(f"   条数: {len(subtitles)}")
    
    if len(subtitles) > 0:
        print(f"   时间范围: {subtitles[0]['start']} --> {subtitles[-1]['end']}")
    
    return len(subtitles)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python subtitle_generator.py <火山引擎结果.json> <审核稿.txt> [输出.srt]")
        sys.exit(1)
    
    volc_path = sys.argv[1]
    draft_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else '简体0721.srt'
    
    generate_subtitle(volc_path, draft_path, output_path)
