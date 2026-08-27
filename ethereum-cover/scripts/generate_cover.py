#!/usr/bin/env python3
"""
以太坊封面生成工具

生成以太坊视频的封面图片，不涉及视频剪辑。
"""

import sys
import os
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ====== 配置 ======
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"
COVER_DIR = "/Users/ai/Documents/video_pipeline/3daily/covers"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"
SKILL_DIR = Path(__file__).parent.parent
ASSETS_DIR = SKILL_DIR / "assets"


def get_rotation_color():
    """获取当天封面颜色（与比特币视频共用同一轮换状态）

    从 4fixed/covers/.cover_rotation_state 读取轮换状态
    该文件由 generate-cover-v2 维护，确保以太坊与比特币颜色一致
    """
    # 从 4fixed 目录读取（与比特币视频共用的轮换状态）
    state_file = Path("/Users/ai/Documents/video_pipeline/4fixed/covers/.cover_rotation_state")

    if state_file.exists():
        today = datetime.now().strftime('%Y-%m-%d')
        with open(state_file, 'r') as f:
            state = json.load(f)
        if today in state:
            return state[today]
    # 如果没有找到今天的颜色，返回默认值
    return 'green'


def get_latest_final_txt():
    """获取最新的 final.txt 文件"""
    txt_files = []
    for file in os.listdir(SUBTITLE_DIR):
        if file == 'final.txt':
            file_path = os.path.join(SUBTITLE_DIR, file)
            txt_files.append((file_path, os.path.getmtime(file_path)))

    if not txt_files:
        raise RuntimeError(f"❌ 在 {SUBTITLE_DIR} 中未找到 final.txt")

    txt_files.sort(key=lambda x: x[1], reverse=True)
    return txt_files[0][0]


def parse_srt(srt_path):
    """解析 SRT 字幕文件

    返回: [(start_ms, end_ms, text), ...]
    """
    import re
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
                return start

    # 兜底：查找包含过渡词 + 以太坊的组合
    transition_words = ['我们', '那', '再看', '接下来', '然后']
    eth_keywords = ['以太坊', '以太']

    for start, end, text in subtitles:
        if start < skip_first_ms:
            continue

        has_transition = any(tw in text for tw in transition_words)
        has_eth = any(ek in text for ek in eth_keywords)

        if has_transition and has_eth:
            return start

    return None


def generate_ethereum_titles(final_txt_path):
    """调用 DeepSeek 生成以太坊封面文字和视频标题

    返回: (cover_candidates, video_title)
    """
    # 读取以太坊片段的字幕内容（而不是完整文稿）
    try:
        # 查找最新的简体字幕文件
        import glob
        srt_pattern = os.path.join(SUBTITLE_DIR, "简体*.srt")
        srt_files = glob.glob(srt_pattern)

        if not srt_files:
            raise RuntimeError(f"❌ 在 {SUBTITLE_DIR} 中未找到简体字幕")

        srt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        srt_path = srt_files[0]

        # 解析字幕
        subtitles = parse_srt(srt_path)

        # 找到以太坊开始时间
        eth_start_ms = find_ethereum_start(subtitles)
        if eth_start_ms is None:
            raise RuntimeError("❌ 未找到以太坊片段")

        # 只提取以太坊片段的字幕文本
        eth_texts = []
        for start, end, text in subtitles:
            if start >= eth_start_ms:
                eth_texts.append(text)

        content = '\n'.join(eth_texts)

        if len(content.strip()) < 50:
            raise RuntimeError("❌ 以太坊片段内容太短")

    except Exception as e:
        print(f"⚠️  读取以太坊片段失败: {e}")
        print(f"📋 回退到完整文稿")
        try:
            with open(final_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = "以太坊行情分析"

    # 去掉可能触发审核的敏感词
    content = content.replace('军长', '分析师').replace('我是军长', '我是分析师')

    # 调用 DeepSeek 生成封面文字候选 + 视频标题
    load_dotenv(SKILL_DIR / ".env")
    api_key = os.getenv('DEEPSEEK_API_KEY')

    if not api_key:
        raise RuntimeError("❌ 未找到 DEEPSEEK_API_KEY")

    import requests

    prompt = f"""你是币圈 YouTube 频道的标题专家。

请根据以下**以太坊专属片段**的字幕内容，生成以太坊视频的封面文字和视频标题。

**重要**：这是从完整视频中提取的**以太坊片段**，内容只涉及以太坊，不包含比特币。

## 以太坊片段字幕内容
{content}

## 输出要求
请严格按以下 JSON 格式输出（不要有其他内容）：
{{
  "cover_candidates": [
    "XXXXX",
    "XXXXX",
    "XXXXX"
  ],
  "video_title": "几句话总结以太坊行情"
}}

## 封面文字要求（5字）
1. 严格 5 个中文字符
2. 风格：理性、技术分析、行情判断
3. **禁止使用**：暴涨、暴跌、起飞、机会、必看、震惊、一定、稳赚
4. **禁止使用**：感叹号、表情符号
5. 参考风格：短期见底没、反弹后再跌、关注82阻力、Y浪尾声、等待反弹

## 视频标题要求（60-80字）
直接输出以太坊行情分析内容，要求如下：
- 几句话总结以太坊行情
- **不含**短标题、日期
- **不含**任何括号内容
- **不含**"几句话总结"、"以太坊行情"等引导性词语
- **禁止使用**任何营销、推广内容，如"加入社区"、"社区免费开放"、"关注社区"等
- **禁止使用**引导性结尾，如"祝大家好运"、"拜拜"等
- **禁止提及**社区、群组、联系方式等
- **保留所有标点符号**（冒号、逗号、句号等），不得自动移除
- 内容包括：结构分析、关键点位、风险提示
- 直接输出分析内容本身，不要添加任何说明性前缀或结尾
- 纯粹关注技术分析和行情走势
"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL = "deepseek-chat"

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "temperature": 0.7,
            "max_tokens": 1500,
            "messages": [
                {"role": "system", "content": "你是一个专业的币圈行情分析师。"},
                {"role": "user", "content": prompt}
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()["choices"][0]["message"]["content"].strip()

    # 解析 JSON
    if result.startswith("```"):
        lines = result.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        result = "\n".join(lines).strip()

    data = json.loads(result)

    cover_candidates = data.get("cover_candidates", [])
    video_title = data.get("video_title", "")

    if not cover_candidates or len(cover_candidates) == 0:
        raise RuntimeError("❌ DeepSeek 未返回封面文字候选")

    if not video_title:
        raise RuntimeError("❌ DeepSeek 未返回视频标题")

    return cover_candidates, video_title


def generate_ethereum_cover(cover_text, color, review_mode=False):
    """生成以太坊封面图片

    Args:
        cover_text: 封面文字（5字）
        color: 背景颜色（green/red/blue/yellow）
        review_mode: 审核模式（True=只保存到3daily/covers，False=同时复制到2output）

    Returns:
        cover_path: 封面文件路径（3daily/covers中的路径）
    """
    from PIL import Image, ImageDraw, ImageFont

    # 获取背景图
    bg_file = ASSETS_DIR / f"eth_{color}.png"
    if not bg_file.exists():
        bg_file = ASSETS_DIR / "eth_green.png"

    if not bg_file.exists():
        raise RuntimeError(f"❌ 背景图不存在: {bg_file}")

    os.makedirs(COVER_DIR, exist_ok=True)

    # 打开背景图
    bg = Image.open(bg_file).convert("RGBA")
    draw = ImageDraw.Draw(bg)
    width, height = bg.size

    # 字体配置
    font_configs = [
        ("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc", 0),
        ("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc", 1),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ]

    title_font = None
    for font_path_str, font_index in font_configs:
        font_path = Path(font_path_str).expanduser()
        if font_path.exists():
            try:
                title_font = ImageFont.truetype(str(font_path), 376, index=font_index)
                break
            except:
                continue

    if title_font is None:
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 376)
        except:
            title_font = ImageFont.load_default()

    # 计算文字位置
    title_bbox = draw.textbbox((0, 0), cover_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    # 水平居中
    title_x = (width - title_width) // 2

    # 垂直居中
    top_area_end = 80
    available_space = height - top_area_end
    title_center_y = top_area_end + available_space // 2
    title_y = title_center_y - title_height // 2

    # 绘制文字
    draw.text((title_x, title_y), cover_text, font=title_font, fill=(255, 255, 255))

    # 保存封面
    today = datetime.now()
    month_day = today.strftime("%m%d")

    cover_filename = f"{cover_text}{month_day}.png"
    cover_path = os.path.join(COVER_DIR, cover_filename)
    bg.save(cover_path)

    # 审核模式：只保存到 3daily/covers
    # 正式模式：复制到 2output 文件夹
    if not review_mode:
        cover_path_2output = os.path.join(OUTPUT_DIR, cover_filename)
        shutil.copy2(cover_path, cover_path_2output)
        print(f"\n✅ 以太坊封面生成完成:")
        print(f"   - 封面（3daily/covers）: {cover_path}")
        print(f"   - 封面（2output）: {cover_path_2output}")
        print(f"   - 封面文字: {cover_text}")
    else:
        print(f"\n✅ 以太坊审核封面生成完成:")
        print(f"   - 封面（3daily/covers）: {cover_path}")
        print(f"   - 封面文字: {cover_text}")
        print(f"   - 背景颜色: {color}")
        print(f"   - 审核模式：仅保存到 3daily/covers")

    return cover_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='生成以太坊封面图片')
    parser.add_argument('--cover-text', type=str, help='指定封面文字（5字）')
    parser.add_argument('--color', type=str, help='指定背景颜色（green/red/blue/yellow）')
    parser.add_argument('--review', action='store_true', help='审核模式（只保存到3daily/covers）')
    parser.add_argument('--approve', action='store_true', help='审核通过标志，保存到2output')

    args = parser.parse_args()

    try:
        # 获取 final.txt
        final_txt = get_latest_final_txt()
        print(f"📂 自动找到文稿: {final_txt}")

        # 获取封面颜色
        if args.color:
            color = args.color
            print(f"🎨 使用指定颜色: {color}")
        else:
            color = get_rotation_color()
            print(f"🎨 自动选择颜色: {color}")

        # 如果指定了封面文字，直接生成
        if args.cover_text:
            cover_text = args.cover_text
            print(f"📝 使用指定封面文字: {cover_text}")

            # ⚠️ 重要：只有使用 --approve 参数时才保存到2output
            # 未经审核的封面只保存到3daily/covers
            review_mode = not args.approve

            # 生成封面
            cover_path = generate_ethereum_cover(cover_text, color, review_mode=review_mode)

            if args.approve:
                print(f"\n✅ 审核通过，封面已保存到 2output")
            else:
                print(f"\n⏸️ 审核模式，封面仅保存到 3daily/covers")
                print(f"💡 审核通过后，使用 --approve 参数生成正式封面:")
                print(f"   python3 {sys.argv[0]} --cover-text=\"{cover_text}\" --approve")

            # 同时生成视频标题（用于文件命名）
            print(f"\n💡 提示：视频标题需要在生成视频时单独调用")
            print(f"   使用命令：python3 /path/to/ethereum-video/scripts/generate_ethereum_video.py")

            return

        # 否则，调用 DeepSeek 生成封面文字候选
        print(f"\n🤖 正在生成封面文字和视频标题...")

        cover_candidates, video_title = generate_ethereum_titles(final_txt)

        print(f"\n============================================================")
        print(f"【以太坊封面文字候选】")
        print(f"============================================================")

        for i, candidate in enumerate(cover_candidates, 1):
            print(f"{i}. {candidate}")

        print(f"\n============================================================")
        print(f"【视频标题】")
        print(f"============================================================")
        print(f"{video_title}")

        # 去除视频标题末尾的标点符号
        display_video_title = video_title.rstrip('。')
        # 使用实际日期而非占位符
        today = datetime.now()
        date_str = today.strftime("%m.%d")
        print(f"📌 完整标题: {date_str}以太坊价格今日行情：{display_video_title}（以太坊合约交易）军长")
        print(f"\n💡 审核通过后，运行以下命令生成封面：")
        print(f"   python3 {sys.argv[0]} --cover-text=\"选定的封面文字\"")

        # 生成审核封面（使用第一个候选）
        first_candidate = cover_candidates[0]
        print(f"\n⚠️  非交互环境，使用第1个候选: {first_candidate}")
        cover_path = generate_ethereum_cover(first_candidate, color, review_mode=True)

        print(f"\n⏸️  等待审核...")
        print(f"\n============================================================")
        print(f"【封面文字审核模式】")
        print(f"============================================================")

        print(f"\n✅ 封面文字已选择，等待你的审核...")
        print(f"\n📋 审核信息：")
        print(f"   - 封面文字: {first_candidate}")
        print(f"   - 背景颜色: {color}")
        print(f"   - 视频标题: {video_title}")
        # 使用实际日期而非占位符
        today = datetime.now()
        date_str = today.strftime("%m.%d")
        print(f"   - 📌 完整标题: {date_str}以太坊价格今日行情：{display_video_title}（以太坊合约交易）军长")

        print(f"\n💡 审核通过后，运行以下命令生成封面：")
        print(f"   python3 {sys.argv[0]} --cover-text=\"{first_candidate}\"")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
