#!/usr/bin/env python3
"""
为币种视频生成元数据：封面标题、视频标题、文件重命名

基于币种时间轴和字幕文件，为每个币种（除比特币外）生成：
1. 5字封面标题（显示在控制台）
2. 80字视频标题（包含前后缀，参照 Video3 格式）
3. 重命名视频文件

支持根据资产时间轴筛选字幕内容，避免不同币种内容混淆
"""

import sys
import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 配置
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"


def parse_srt_time(time_str):
    """解析 SRT 时间戳为秒"""
    # Format: HH:MM:SS,mmm
    match = re.match(r'(\d+):(\d+):(\d+),(\d+)', time_str)
    if match:
        h, m, s, ms = match.groups()
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return 0.0


def parse_srt(srt_path):
    """解析 SRT 字幕文件

    返回: [(start_s, end_s, text), ...]
    """
    time_re = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")

    def to_s(h, m, s, ms):
        return ((int(h) * 60 + int(m)) * 60 + int(s)) + int(ms) / 1000

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
                start_s = parse_srt_time(start_str.strip())
                end_s = parse_srt_time(end_str.strip())
                text = '\n'.join(lines[2:])
                subtitles.append((start_s, end_s, text))

    return subtitles


def filter_srt_by_coin(srt_path, coin_name, start_ms, end_ms):
    """提取币种时间轴范围内的所有字幕内容

    资产时间轴已经明确定义了每个币种的独立时段，
    直接提取该时段的所有内容即可。

    Args:
        srt_path: SRT 文件路径
        coin_name: 币种名称（用于日志）
        start_ms: 开始时间（毫秒）
        end_ms: 结束时间（毫秒）

    Returns:
        该时间范围内的所有字幕内容
    """
    start_s = start_ms / 1000
    end_s = end_ms / 1000

    subtitles = parse_srt(srt_path)
    filtered_texts = []

    for start, end, text in subtitles:
        # 检查是否与时间范围重叠
        if end >= start_s and start <= end_s:
            filtered_texts.append(text)

    if not filtered_texts:
        return f"【{coin_name}行情分析】"

    return '\n'.join(filtered_texts)


def get_coin_timeline(timeline_path, coin_name):
    """从资产时间轴获取币种时间范围

    Args:
        timeline_path: assets_timeline.json 路径
        coin_name: 币种名称

    Returns:
        (start_ms, end_ms) 或 None
    """
    with open(timeline_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 币种名称映射
    name_mapping = {
        '以太坊': ['以太坊', 'ETH', '以太'],
        'dydx': ['dydx', 'DYDX'],
        'UNI': ['UNI'],
    }

    target_names = name_mapping.get(coin_name, [coin_name])

    for asset in data.get('segments', []):
        if asset.get('name') in target_names:
            return (asset.get('start_ms', 0), asset.get('end_ms', 0))

    return None


def read_final_txt():
    """读取 final.txt 文件（作为备用）"""
    final_path = os.path.join(SUBTITLE_DIR, "final.txt")
    if os.path.exists(final_path):
        with open(final_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def get_coin_content(coin_name, timeline_path, date_str):
    """获取币种内容（优先使用时间轴筛选的SRT，否则使用final.txt）

    Args:
        coin_name: 币种名称
        timeline_path: 资产时间轴文件路径
        date_str: 日期字符串（MMDD）

    Returns:
        币种内容文本
    """
    # 1. 尝试从资产时间轴获取时间范围并筛选SRT
    if os.path.exists(timeline_path):
        timeline_range = get_coin_timeline(timeline_path, coin_name)

        if timeline_range:
            start_ms, end_ms = timeline_range
            print(f"   📋 使用时间轴筛选内容: {start_ms/1000:.1f}s - {end_ms/1000:.1f}s")

            # 查找最新的简体 SRT 文件
            import glob
            srt_pattern = os.path.join(SUBTITLE_DIR, "简体*.srt")
            srt_files = glob.glob(srt_pattern)

            if srt_files:
                srt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                srt_path = srt_files[0]

                # 筛选字幕内容
                filtered_content = filter_srt_by_coin(srt_path, coin_name, start_ms, end_ms)

                if len(filtered_content.strip()) > 50:
                    return filtered_content
                else:
                    print(f"   ⚠️  筛选内容过短（{len(filtered_content)}字），回退到完整文稿")
            else:
                print(f"   ⚠️  未找到 SRT 文件，回退到完整文稿")

    # 2. 回退到读取 final.txt
    print(f"   📋 使用完整文稿（final.txt）")
    final_content = read_final_txt()
    if final_content:
        return final_content

    # 3. 最终回退
    return f"{coin_name}行情分析"


def call_deepseek_for_titles(coin_name, content):
    """调用 DeepSeek 生成标题"""
    import os
    import requests
    from dotenv import load_dotenv
    from pathlib import Path

    # 加载 .env 文件
    SKILL_DIR = Path(__file__).parent.parent
    load_dotenv(SKILL_DIR / ".env")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("❌ 未找到 DEEPSEEK_API_KEY 环境变量")

    # 过滤敏感词（避免触发 DeepSeek 内容审核）
    content = content.replace('军长', '分析师').replace('我是军长', '我是分析师')

    prompt = f"""你现在是一个币圈行情分析视频的标题专家。

## 任务
为币种 **{coin_name}** 生成两个标题：
1. **封面标题**：5个字，用于视频封面
2. **视频标题**：80-100字，用于视频平台（需包含完整分析要点）

## 视频内容（已筛选，仅包含该币种的分析内容）
{content}

## 要求
### 封面标题（5字）
- 必须正好 5 个字
- 偏交易、行情、走势判断
- 不使用营销、夸张、诱导性词汇
- 不出现违规金融承诺类表述
- 参考风格：短期见底没、反弹后再跌、关注82阻力、Y浪尾声、等待反弹

### 视频标题（80-100字）
- 几句话总结 {coin_name} 的行情分析
- 包含主要分析要点（结构、趋势线、关键位置等）
- 保留所有标点符号（冒号、逗号、句号等）
- 不含短标题、日期
- 不含括号内容
- **禁止使用**任何营销、推广内容，如"加入社区"、"社区免费开放"、"关注社区"、"有需要的伙伴欢迎加入"等
- **禁止使用**引导性结尾，如"祝大家好运"、"拜拜"等
- **禁止提及**社区、群组、联系方式等
- 纯粹关注技术分析和行情走势

## 输出格式（严格按此 JSON 格式，不要有其他内容）：
{{
  "cover_title": "（5字封面标题）",
  "video_title": "（80-100字视频标题，保留所有标点）"
}}

## 封面标题参考
- 短期见底没
- 反弹后再跌
- 关注82阻力
- Y浪尾声
- 等待反弹
- 多头抵抗增强
- 空头动能衰竭

## 禁止词汇
暴涨、暴跌、起飞、机会、必看、震惊、一定、稳赚
"""

    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的币圈行情分析标题专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
    )

    if response.status_code != 200:
        raise Exception(f"DeepSeek API 调用失败: {response.status_code} {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # 解析 JSON
    try:
        titles = json.loads(content)
        cover_title = titles.get("cover_title", "").strip()
        video_title = titles.get("video_title", "").strip()

        # 验证封面标题字数
        if len(cover_title) != 5:
            print(f"⚠️  警告：封面标题不是5个字（{len(cover_title)}字）: {cover_title}")

        return cover_title, video_title
    except json.JSONDecodeError as e:
        print(f"❌ 解析 DeepSeek 返回失败: {e}")
        print(f"原始返回: {content}")
        raise


def read_final_txt():
    """读取 final.txt 文件"""
    final_path = os.path.join(SUBTITLE_DIR, "final.txt")
    if os.path.exists(final_path):
        with open(final_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def generate_video_title(coin_name, video_title_content, date_str):
    """生成完整的视频标题（参照 Video3 格式）

    Video3 格式：MM.DD比特币价格今日行情：{内容}，（比特币合约交易）军长

    Args:
        coin_name: 币种名称
        video_title_content: DeepSeek 生成的标题内容
        date_str: 日期字符串（MMDD）
    """
    # 格式化日期
    formatted_date = f"{date_str[:2]}.{date_str[2:]}"

    # 去除内容末尾的句号
    if video_title_content.endswith('。'):
        video_title_content = video_title_content[:-1]

    # 构建完整标题（后缀前不加标点）
    full_title = f"{formatted_date}{coin_name}价格今日行情：{video_title_content}（{coin_name}合约交易）军长"

    return full_title


def get_unique_filename(path):
    """生成唯一文件名，避免覆盖

    Args:
        path: 原始路径

    Returns:
        不冲突的文件路径
    """
    base, ext = os.path.splitext(path)
    candidate = path
    index = 1

    while os.path.exists(candidate):
        candidate = f"{base}_{index}{ext}"
        index += 1

    return candidate


def rename_video_file(old_path, new_title, date_str, overwrite=False):
    """重命名视频文件

    Args:
        old_path: 原文件路径
        new_title: 新标题
        date_str: 日期字符串
        overwrite: 是否覆盖已存在的文件（默认 False）

    Returns:
        new_path: 新文件路径
    """
    # 提取文件扩展名
    ext = os.path.splitext(old_path)[1]

    # 生成新文件名（确保后缀不被截断）
    # macOS 文件名长度限制约为 255 字节，中文占用更多
    max_bytes = 200

    # 分离标题内容和后缀（格式：内容（币种合约交易）军长）
    # 找到最后一个左括号，保留后缀完整
    suffix_start = new_title.rfind('（')
    if suffix_start > 0:
        title_content = new_title[:suffix_start]
        title_suffix = new_title[suffix_start:]
    else:
        # 如果找不到括号，全部作为内容
        title_content = new_title
        title_suffix = ''

    # 计算各部分字节数
    suffix_bytes = len(title_suffix.encode('utf-8'))
    ext_bytes = len(ext.encode('utf-8'))

    # 计算标题内容可用的最大字节数
    available_bytes = max_bytes - suffix_bytes - ext_bytes

    # 如果标题内容太长，截断（保留字节限制内）
    if available_bytes > 0:
        content_encoded = title_content.encode('utf-8')
        if len(content_encoded) > available_bytes:
            # 截断到可用字节数
            truncated_bytes = content_encoded[:available_bytes]
            # 解码并去除可能的不完整字符
            title_content = truncated_bytes.decode('utf-8', errors='ignore')

    # 拼接完整文件名：截断后的内容 + 后缀 + 扩展名
    new_filename = title_content + title_suffix + ext

    # 构建新路径
    dir_path = os.path.dirname(old_path)
    new_path = os.path.join(dir_path, new_filename)

    # 重命名文件
    if os.path.exists(new_path):
        if overwrite:
            print(f"   ⚠️  目标文件已存在，将覆盖: {new_filename}")
            os.remove(new_path)
        else:
            print(f"   ⚠️  目标文件已存在，生成唯一文件名")
            new_path = get_unique_filename(new_path)
            new_filename = os.path.basename(new_path)

    os.rename(old_path, new_path)

    return new_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='为币种视频生成元数据')
    parser.add_argument('--timeline', help='资产时间轴 JSON 文件路径')
    parser.add_argument('--coin', help='指定币种名称（只处理该币种）')
    parser.add_argument('--cover-title', help='指定封面标题（跳过 AI 生成）')
    parser.add_argument('--video-title', help='指定视频标题内容（跳过 AI 生成）')
    parser.add_argument('--no-rename', action='store_true', help='不重命名视频文件')
    parser.add_argument('--overwrite', action='store_true', help='允许覆盖已存在的视频文件')

    args = parser.parse_args()

    # 读取资产时间轴
    if args.timeline:
        timeline_path = args.timeline
    else:
        timeline_path = os.path.join(SUBTITLE_DIR, "assets_timeline.json")

    if not os.path.exists(timeline_path):
        print(f"❌ 资产时间轴文件不存在: {timeline_path}")
        print("   请先运行 analyze-assets skill")
        sys.exit(1)

    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)

    # 读取 final.txt
    final_content = read_final_txt()
    if not final_content:
        print("⚠️  未找到 final.txt，将使用基础内容生成标题")

    # 获取日期
    date_str = timeline_data.get("date", "")
    if date_str:
        # 从 YYYY-MM-DD 转换为 MMDD
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date_str = date_obj.strftime("%m%d")
    else:
        date_str = datetime.now().strftime("%m%d")

    print(f"📅 日期: {date_str}")
    print(f"📋 资产时间轴: {timeline_path}")

    # 处理每个币种（跳过比特币）
    assets = timeline_data.get("segments", [])
    processed_count = 0

    for asset in assets:
        coin_name = asset["name"]

        # 跳过比特币
        if coin_name == "比特币":
            continue

        # 如果指定了币种，只处理该币种
        if args.coin and coin_name != args.coin:
            continue

        print(f"\n{'='*80}")
        print(f"🎬 正在处理 {coin_name}")
        print(f"{'='*80}")

        # 查找对应的视频文件
        # 先尝试精确匹配（简单格式）
        video_pattern = os.path.join(OUTPUT_DIR, f"{date_str}{coin_name}.mp4")
        video_files = [video_pattern] if os.path.exists(video_pattern) else []

        # 如果没找到，使用模糊匹配（查找文件名中包含币种名称的视频）
        if not video_files:
            import glob
            # 匹配包含币种名称的 .mp4 文件（不要求在结尾，不区分大小写）
            search_pattern = os.path.join(OUTPUT_DIR, "*.mp4")
            all_matches = glob.glob(search_pattern)

            # 过滤掉主视频（Video1/2/3/4）
            main_videos = ['1繁体', '2简体', '3字幕', '4字幕']
            asset_videos = [f for f in all_matches if not any(mv in os.path.basename(f) for mv in main_videos)]

            # 不区分大小写匹配币种名称
            coin_name_lower = coin_name.lower()
            video_files = [f for f in asset_videos if coin_name_lower in os.path.basename(f).lower()]

            # 优先选择最新的文件
            if video_files:
                video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                video_files = [video_files[0]]

        if not video_files:
            print(f"   ⚠️  未找到 {coin_name} 的视频文件，跳过")
            continue

        video_path = video_files[0]
        print(f"   📁 视频文件: {os.path.basename(video_path)}")

        # 生成标题
        if args.cover_title and args.video_title:
            # 使用指定的标题
            cover_title = args.cover_title
            video_title_content = args.video_title
            print(f"   📝 使用指定封面标题: {cover_title}")
            print(f"   📝 使用指定视频标题: {video_title_content}")
        else:
            # 调用 DeepSeek 生成标题
            print(f"   🤖 正在生成标题...")
            try:
                # 使用资产时间轴筛选的内容（而不是整个 final.txt）
                content = get_coin_content(coin_name, timeline_path, date_str)
                cover_title, video_title_content = call_deepseek_for_titles(coin_name, content)

                # 验证封面标题
                if len(cover_title) != 5:
                    print(f"   ⚠️  警告：封面标题不是5个字（{len(cover_title)}字）: {cover_title}")

                print(f"   📝 封面标题: {cover_title}")
                print(f"   📝 视频标题内容: {video_title_content}")
            except Exception as e:
                print(f"   ❌ 生成标题失败: {e}")
                continue

        # 生成完整视频标题
        full_video_title = generate_video_title(coin_name, video_title_content, date_str)
        print(f"   📌 完整视频标题: {full_video_title}")

        # 重命名视频文件
        if not args.no_rename:
            try:
                print(f"   📝 正在重命名视频文件...")
                new_path = rename_video_file(video_path, full_video_title, date_str, overwrite=args.overwrite)
                print(f"   ✅ 视频已重命名: {os.path.basename(new_path)}")
            except Exception as e:
                print(f"   ❌ 重命名失败: {e}")
        else:
            print(f"   ℹ️  跳过重命名（--no-rename）")

        processed_count += 1

    print(f"\n{'='*80}")
    print(f"✅ 处理完成！共处理 {processed_count} 个币种")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
