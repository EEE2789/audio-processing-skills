#!/usr/bin/env python3
"""
分析币圈视频中提到的所有币种和股票及其起始时间

重写版本：基于"资产切换信号"来分段，而不是过滤"连接话"
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# 配置
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"

# 资产名称白名单和别名
ASSET_ALIASES = {
    '比特币': ['BTC', 'Bitcoin', '比特币', '大饼', 'btc'],
    '以太坊': ['ETH', 'Ethereum', '以太坊', '以太', 'eth'],
    '黄金': ['黄金', 'Gold', '金', '黄金'],
    'NEAR': ['NEAR', 'Near', 'near'],
    'SOL': ['SOL', 'Sol', 'sol', 'Solana'],
    'ZEC': ['ZEC', 'Zec', 'zec'],
    'XLM': ['XLM', 'xlm', 'Stellar', '恒星币'],
    'AAVE': ['AAVE', 'Aave', 'aave', 'AAAVE', 'aAAVE'],  # 添加常见的ASR识别变体
    'MSTR': ['MSTR', 'mstr', 'MicroStrategy', '微策略'],
    'dydx': ['dydx', 'DYDX', 'dYdX'],
    'UNI': ['UNI', 'Uni', 'uni'],
    'CRCL': ['CRCL', 'CIRCLE', 'Circle'],
}

def normalize_asset_name(name):
    """标准化资产名称"""
    if not name:
        return None
    name = name.strip()
    name_lower = name.lower()

    # 检查别名映射
    for canonical, aliases in ASSET_ALIASES.items():
        for alias in aliases:
            if alias.lower() == name_lower:
                return canonical

    # 如果不在别名表，返回 None
    return None


def parse_srt_time(time_str):
    """解析 SRT 时间戳为毫秒"""
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    return total_ms


def format_time(ms):
    """格式化毫秒为 SRT 时间格式"""
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(srt_path):
    """解析 SRT 字幕文件"""
    time_re = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")

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
                start_str, end_str = parts
                start_ms = parse_srt_time(start_str.strip())
                end_ms = parse_srt_time(end_str.strip())
                text = '\n'.join(lines[2:])
                subtitles.append((start_ms, end_ms, text))

    return subtitles


def get_latest_files():
    """获取最新的字幕文件"""
    import glob
    srt_pattern = os.path.join(SUBTITLE_DIR, "简体*.srt")
    srt_files = glob.glob(srt_pattern)
    srt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return srt_files[0] if srt_files else None


def merge_consecutive_segments(segments):
    """合并连续的同名资产段"""
    if not segments:
        return []

    merged = []
    current = segments[0].copy()

    for seg in segments[1:]:
        # 如果是同名段，合并
        if seg['asset'] == current['asset']:
            # 保持开始时间不变，更新结束时间
            current['end_ms'] = seg['end_ms']
            # 更新触发信号为最后一段的
            current['trigger'] = seg['trigger']
        else:
            # 不同资产，保存当前段，开始新段
            merged.append(current)
            current = seg.copy()

    merged.append(current)
    return merged


def find_asset_segments(subtitles):
    """基于资产切换信号来分段

    返回：list of {'asset': str, 'start_ms': int, 'end_ms': int, 'trigger': str}
    """
    segments = []

    # 资产切换信号模式
    # 格式：(正则模式, 提取资产名的组索引, 是否结束信号)
    switch_patterns = [
        # 明确的切换信号
        (r'(?:所以|那|好|OK|好吧).*这里面(比特币|以太坊|黄金)', 1, False),
        (r'(比特币|以太坊)说完了', 0, True),  # 结束信号
        (r'那(比特币|以太坊)(?:我们)?(?:再|来)?(?:看|讲)?(?:一下)?', 1, False),
        (r'(比特币|以太坊|黄金)(?:这边|整体|也是|的结构)', 0, False),
        (r'目前整体(比特币|以太坊|黄金)', 1, False),
        (r'我们(?:再|来)?(?:再|来)?(?:看|讲)一下(比特币|以太坊|黄金)', 1, False),
        (r'(?:我们|那)(?:再|来)?(?:再|来)?看一下(比特币|以太坊|黄金)', 1, False),
        (r'我们今天(?:再|来)?(?:再|来)?看一下(黄金)', 1, False),  # "我们今天来看一下黄金"
    ]

    current_asset = None
    current_start_ms = None

    for idx, (start_ms, end_ms, text) in enumerate(subtitles):
        matched = False
        matched_asset = None

        for pattern, group_idx, is_end_signal in switch_patterns:
            match = re.search(pattern, text)
            if match:
                raw_asset = match.group(group_idx)
                asset_name = normalize_asset_name(raw_asset)

                if asset_name:
                    matched = True
                    matched_asset = asset_name

                    # 如果是结束信号
                    if is_end_signal:
                        if current_asset and current_start_ms is not None:
                            segments.append({
                                'asset': current_asset,
                                'start_ms': current_start_ms,
                                'end_ms': start_ms,
                                'trigger': text.strip()[:50]
                            })
                            print(f"   📍 {current_asset} 段结束 @ {format_time(start_ms)} (触发: {text.strip()[:30]})")
                        current_asset = None
                        current_start_ms = None
                    else:
                        # 切换到新资产
                        if current_asset and current_start_ms is not None:
                            # 结束当前资产段
                            segments.append({
                                'asset': current_asset,
                                'start_ms': current_start_ms,
                                'end_ms': start_ms,
                                'trigger': text.strip()[:50]
                            })
                            print(f"   📍 {current_asset} 段结束 @ {format_time(start_ms)}")

                        # 开始新资产段
                        current_asset = asset_name
                        current_start_ms = start_ms
                        print(f"   📍 {asset_name} 段开始 @ {format_time(start_ms)} (触发: {text.strip()[:30]})")
                    break

        # 如果还没匹配到任何资产，检查开头是否提到比特币
        if not matched and current_asset is None and idx < 10:
            if '比特币' in text or 'BTC' in text:
                current_asset = '比特币'
                current_start_ms = start_ms
                print(f"   📍 {current_asset} 段开始 @ {format_time(start_ms)} (开头)")

    # 处理最后一个资产段
    if current_asset and current_start_ms is not None and subtitles:
        last_end_ms = subtitles[-1][1]
        segments.append({
            'asset': current_asset,
            'start_ms': current_start_ms,
            'end_ms': last_end_ms,
            'trigger': '视频结束'
        })
        print(f"   📍 {current_asset} 段结束 @ {format_time(last_end_ms)} (视频结束)")

    return segments


def find_intro_time(subtitles):
    """查找开头自我介绍的时间范围"""
    intro_patterns = [r'我是军长']

    for start_ms, end_ms, text in subtitles:
        if any(re.search(p, text) for p in intro_patterns):
            return {
                "start_time": "00:00:00,000",
                "start_ms": 0,
                "end_time": format_time(end_ms),
                "end_ms": end_ms,
                "description": "开头自我介绍"
            }

    # 默认前3条字幕
    if len(subtitles) >= 3:
        end_ms = subtitles[2][1]
    else:
        end_ms = subtitles[0][1] if subtitles else 5000

    return {
        "start_time": "00:00:00,000",
        "start_ms": 0,
        "end_time": format_time(end_ms),
        "end_ms": end_ms,
        "description": "开头"
    }


def generate_timeline_table(segments, intro):
    """生成时间轴表格"""
    if not segments:
        return "# ⚠️ 未找到任何资产提及\n\n视频可能没有明确提到具体的币种或股票名称。"

    output = []
    output.append("## 📊 今天视频中提到的资产及时间范围\n")
    output.append("\n")
    output.append("| 序号 | 资产 | 开始时间 | 结束时间 | 时长 | 说明 |")
    output.append("|------|------|----------|----------|------|------|")

    for idx, seg in enumerate(segments, 1):
        start_ms = seg['start_ms']
        end_ms = seg['end_ms']
        start_str = format_time(start_ms)
        end_str = format_time(end_ms)

        duration_ms = end_ms - start_ms
        duration_s = duration_ms / 1000
        if duration_s >= 60:
            duration_str = f"{duration_s/60:.1f}分钟"
        else:
            duration_str = f"{duration_s:.1f}秒"

        description = f"触发: {seg['trigger'][:20]}"

        output.append(f"| {idx} | **{seg['asset']}** | {start_str} | {end_str} | {duration_str} | {description} |")

    # 添加详细时间轴
    output.append("\n---\n")
    output.append("### 详细时间轴\n")

    for idx, seg in enumerate(segments, 1):
        start_ms = seg['start_ms']
        end_ms = seg['end_ms']
        start_str = format_time(start_ms)
        end_str = format_time(end_ms)
        duration_s = (end_ms - start_ms) / 1000

        output.append(f"\n{idx}. **{seg['asset']}**")
        output.append(f"   - 时间范围：{start_str} - {end_str}")
        output.append(f"   - 时长：{duration_s:.1f}秒")
        output.append(f"   - 触发信号：{seg['trigger']}")

    output.append("\n---\n")

    # 统计
    from collections import Counter
    asset_counts = Counter(seg['asset'] for seg in segments)
    total_duration = sum(seg['end_ms'] - seg['start_ms'] for seg in segments) / 1000

    output.append(f"\n**总结**：")
    output.append(f"- 共 {len(segments)} 个分析段落")
    output.append(f"- 资产总时长：{total_duration:.1f}秒")

    if len(asset_counts) > 1:
        output.append(f"\n各资产段数：")
        for asset, count in asset_counts.items():
            segments_for_asset = [s for s in segments if s['asset'] == asset]
            total_asset_duration = sum(s['end_ms'] - s['start_ms'] for s in segments_for_asset) / 1000
            output.append(f"- **{asset}**: {count}段, 共{total_asset_duration:.1f}秒")
    else:
        output.append(f"\n主要资产：**{list(asset_counts.keys())[0]}**")

    return "\n".join(output)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='分析币圈视频中的资产时间轴')
    parser.add_argument('srt_path', nargs='?', help='字幕文件路径（可选）')
    args = parser.parse_args()

    # 获取字幕文件
    if args.srt_path:
        srt_path = args.srt_path
    else:
        srt_path = get_latest_files()
        if not srt_path:
            print("❌ 未找到字幕文件")
            sys.exit(1)

    print(f"📂 字幕文件: {srt_path}")
    print()
    print("🔍 正在解析字幕...")
    subtitles = parse_srt(srt_path)
    print(f"   找到 {len(subtitles)} 条字幕")

    print()
    print("🔍 正在分析资产切换信号...")
    segments = find_asset_segments(subtitles)

    # 合并连续的同名段
    print()
    print("🔍 正在合并连续的同名段...")
    segments = merge_consecutive_segments(segments)
    for seg in segments:
        print(f"   📍 {seg['asset']}: {format_time(seg['start_ms'])} - {format_time(seg['end_ms'])}")

    print()
    print("🔍 正在查找开头自我介绍...")
    intro = find_intro_time(subtitles)
    print(f"   找到开头介绍: {intro['start_time']} - {intro['end_time']}")

    # 生成表格
    print()
    print("=" * 80)
    timeline_table = generate_timeline_table(segments, intro)
    print(timeline_table)
    print("=" * 80)

    # 保存到 JSON 文件
    output_dir = SUBTITLE_DIR
    output_json = os.path.join(output_dir, "assets_timeline.json")

    import json

    # 从字幕文件名提取日期
    date_match = re.search(r'(\d{2})\.?(\d{2})', os.path.basename(srt_path))
    if date_match:
        month, day = date_match.groups()
        date_str = f"2026-{month.zfill(2)}-{day.zfill(2)}"
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 构建 JSON 数据
    assets_data = []
    for seg in segments:
        start_ms = seg['start_ms']
        end_ms = seg['end_ms']
        assets_data.append({
            "name": seg['asset'],
            "start_time": format_time(start_ms),
            "end_time": format_time(end_ms),
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": end_ms - start_ms,
            "trigger": seg['trigger']
        })

    json_data = {
        "date": date_str,
        "intro": intro,
        "segments": assets_data,
        "total_segments": len(segments)
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 资产时间轴已保存到: {output_json}")


if __name__ == "__main__":
    main()
