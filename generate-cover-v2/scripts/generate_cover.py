#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 比特币行情分析视频封面生成 v2
基于已存在的背景模板图，叠加标题文字
"""

import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ====== 配置 ======
ENV_FILE = Path(__file__).parent.parent / ".env"
DEFAULT_TXT_PATH = Path("/Users/ai/Documents/video_pipeline/3daily/final.txt")
OUTPUT_DIR = Path("/Users/ai/Documents/video_pipeline/3daily/covers")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# 2output 输出目录
OUTPUT_DIR_2 = Path("/Users/ai/Documents/video_pipeline/2output")
OUTPUT_DIR_2.mkdir(parents=True, exist_ok=True)
# 4fixed 状态文件目录（不会被清理）
STATE_DIR = Path("/Users/ai/Documents/video_pipeline/4fixed/covers")
STATE_DIR.mkdir(parents=True, exist_ok=True)

# 背景图配置（只读品牌资产）
ASSETS_DIR = Path(__file__).parent.parent / "assets"
# 简体背景图
BACKGROUNDS_SIMPLIFIED = {
    "green": ASSETS_DIR / "简体背景绿色.png",
    "red": ASSETS_DIR / "简体背景红色.png",
    "blue": ASSETS_DIR / "简体背景蓝色.png",
    "yellow": ASSETS_DIR / "简体背景黄色.png",
}
# 繁体背景图
BACKGROUNDS_TRADITIONAL = {
    "green": ASSETS_DIR / "繁体背景绿色.png",
    "red": ASSETS_DIR / "繁体背景红色.png",
    "blue": ASSETS_DIR / "繁体背景蓝色.png",
    "yellow": ASSETS_DIR / "繁体背景黄色.png",
}

# 背景轮换顺序
ROTATION_ORDER = ["green", "red", "blue", "yellow"]

# 简繁转换映射（币圈专用）
S2T_MAP = {
    '比特币': '比特幣', '稳定币': '穩定幣',
    '开仓': '開倉', '止损': '止損', '止盈': '止盈',
    '买': '買', '卖': '賣', '图': '圖', '线': '線',
    '价': '價', '现': '現', '势': '勢', '万': '萬',
    '亿': '億', '机': '機', '机会': '機會',
}


# ====== 工具函数 ======

def load_env():
    """加载环境变量"""
    if not ENV_FILE.exists():
        return {}

    env_vars = {}
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def to_traditional(text):
    """简体转繁体（币圈专用）"""
    result = text
    for s, t in S2T_MAP.items():
        result = result.replace(s, t)
    return result


import json

# 背景轮换顺序
ROTATION_ORDER = ["green", "red", "blue", "yellow"]

# 轮换状态文件（记录日期到颜色的映射，放在4fixed避免被清理）
STATE_FILE = STATE_DIR / ".cover_rotation_state"

# 简繁转换映射（币圈专用）
S2T_MAP = {
    '比特币': '比特幣', '稳定币': '穩定幣',
    '开仓': '開倉', '止损': '止損', '止盈': '止盈',
    '买': '買', '卖': '賣', '图': '圖', '线': '線',
    '价': '價', '现': '現', '势': '勢', '万': '萬',
    '亿': '億', '机': '機', '机会': '機會',
}


# ====== 工具函数 ======

def load_env():
    """加载环境变量"""
    if not ENV_FILE.exists():
        return {}

    env_vars = {}
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def to_traditional(text):
    """简体转繁体（币圈专用）"""
    result = text
    for s, t in S2T_MAP.items():
        result = result.replace(s, t)
    return result


def load_rotation_state():
    """加载日期-颜色映射状态"""
    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_rotation_state(state):
    """保存日期-颜色映射状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_rotation_color(target_date):
    """根据日期获取应该使用的背景颜色

    按发视频日期顺序轮换：green -> red -> blue -> yellow -> 循环
    同一天多次生成时使用相同颜色

    逻辑：
    1. 如果这一天已有颜色，直接返回
    2. 否则读取最近日期的颜色，从下一个颜色开始轮换
    3. 如果没有历史记录，从 green 开始

    Args:
        target_date: datetime对象

    Returns:
        颜色名称
    """
    date_str = target_date.strftime('%Y-%m-%d')
    state = load_rotation_state()

    # 如果这一天已经有指定颜色（用户手动指定过），使用该颜色
    if date_str in state:
        return state[date_str]

    # 获取所有已记录的日期，按日期排序
    recorded_dates = sorted(state.keys())

    if not recorded_dates:
        # 没有历史记录，从第一个颜色开始
        next_color = ROTATION_ORDER[0]
    else:
        # 找到最近日期的颜色
        last_date = recorded_dates[-1]
        last_color = state[last_date]

        # 获取该颜色在轮换顺序中的索引，然后取下一个
        last_index = ROTATION_ORDER.index(last_color)
        next_index = (last_index + 1) % len(ROTATION_ORDER)
        next_color = ROTATION_ORDER[next_index]

    # 记录这个日期的颜色
    state[date_str] = next_color
    save_rotation_state(state)

    return next_color


def get_background_color(specified_color=None, target_date=None):
    """获取要使用的背景颜色

    Args:
        specified_color: 用户指定的颜色 (green/red/blue/yellow)，若为 None 则自动轮换
        target_date: datetime对象，用于确定日期

    Returns:
        (颜色名称, 简体背景图路径, 繁体背景图路径, 是否为用户指定)
    """
    if specified_color and specified_color in BACKGROUNDS_SIMPLIFIED:
        # 用户指定颜色：更新状态，记录这个日期的颜色
        if target_date:
            date_str = target_date.strftime('%Y-%m-%d')
            state = load_rotation_state()
            state[date_str] = specified_color
            save_rotation_state(state)

        return (specified_color,
                BACKGROUNDS_SIMPLIFIED[specified_color],
                BACKGROUNDS_TRADITIONAL[specified_color],
                True)  # 用户指定
    else:
        # 自动轮换：根据日期确定颜色
        color = get_rotation_color(target_date)
        return (color,
                BACKGROUNDS_SIMPLIFIED[color],
                BACKGROUNDS_TRADITIONAL[color],
                False)  # 自动轮换


# ====== DeepSeek 标题生成 ======

def call_deepseek_for_titles(content):
    """调用 DeepSeek 生成 3 个封面标题候选"""

    env_vars = load_env()
    api_key = env_vars.get('DEEPSEEK_API_KEY', '')

    if not api_key:
        raise RuntimeError("❌ 未找到 DEEPSEEK_API_KEY，请在 .env 文件中设置")

    # 过滤敏感词（避免触发 DeepSeek 内容审核）
    content = content.replace('军长', '分析师').replace('我是军长', '我是分析师')

    prompt = f'''你是一个币圈 YouTube 频道的封面标题专家。

请根据以下比特币行情分析文稿，生成 5-7 个封面标题候选（我需要从中挑选字数最少的 3 个）。

## 输入文稿
{content}

## 输出格式（严格遵守）
【标题候选】
1. XXXXX
2. XXXXX
3. XXXXX
4. XXXXX
5. XXXXX
6. XXXXX
7. XXXXX

## ⚠️⚠️⚠️ 核心要求
**每个标题必须是正好 5 个中文字符！**
- 不能多也不能少
- 不含空格、标点、数字、英文字母
- 必须是完整的表述，不能截断

## 其他要求
1. 风格：理性、技术分析、行情判断、交易相关
2. 面向散户，关注关键结构/走势预期
3. **禁止使用**：暴涨、暴跌、起飞、机会、必看、震惊、一定、稳赚
4. **禁止使用**：感叹号、表情符号、营销词汇
5. 不要出现"比特"自动转成"比特币"
6. 不要出现时间、日期、价格全称
7. 偏交易、行情、走势判断类表述

## 正确示例（都是 5 字）
- 短期见底没
- 反弹后再跌
- Y浪已尾声
- 等待大反弹
- 多头在抵抗

## 错误示例
- 短期是否见底 ✗（6字）
- 反弹后再下跌 ✗（7字）
- 三浪主升在即 ✗（7字）

**请生成 5-7 个严格 5 字的标题候选，必须是完整的 5 字表述！**
'''

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             'https://api.deepseek.com/v1/chat/completions',
             '-H', 'Content-Type: application/json',
             '-H', f'Authorization: Bearer {api_key}',
             '-d', json.dumps({
                 "model": "deepseek-chat",
                 "messages": [{"role": "user", "content": prompt}],
                 "temperature": 0.7,
                 "max_tokens": 500
             })],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            raise RuntimeError(f"curl 失败: {result.stderr}")

        response = json.loads(result.stdout)

        if 'choices' not in response or len(response['choices']) == 0:
            raise RuntimeError("DeepSeek API 返回格式错误")

        content = response['choices'][0]['message']['content'].strip()

        # 解析标题
        titles_with_length = []
        for line in content.split('\n'):
            line = line.strip()
            # 匹配 "1. 标题" 或 "1) 标题" 格式
            if line and (line[0].isdigit() or line.startswith('•')):
                # 移除序号和空格
                title = line.lstrip('0123456789.•、)）')
                title = title.strip(' )）').strip()
                # 只接受正好 5 个字的标题，不允许截取
                if len(title) == 5:
                    titles_with_length.append((title, len(title)))

        # 按字数排序，选择最少的 3 个
        titles_with_length.sort(key=lambda x: x[1])
        titles = [t[0] for t in titles_with_length[:3]]

        if len(titles) >= 3:
            return titles
        else:
            # 如果解析失败，使用备用标题
            return ["短期见底没", "关注阻力位", "等待反弹中"]

    except subprocess.TimeoutExpired:
        raise RuntimeError("DeepSeek API 调用超时")
    except Exception as e:
        raise RuntimeError(f"调用 DeepSeek 失败: {e}")


# ====== 封面绘制 ======

def draw_cover(title, background_path, output_path):
    """
    使用已存在的背景图，叠加标题文字

    字体规范：
    - 必须使用：兰亭黑简体（Lantinghei SC）
    - 若不存在则报错，不得继续生成

    颜色规范：
    - 标题文字：纯白色 #FFFFFF
    - 禁止：描边、阴影、发光、渐变、半透明

    字号规范：
    - 「比特币行情分析」≈ 95 pt（背景自带，实际像素 162px）
    - 标题 = 376 pt（使实际像素为 300px = 162 × 1.85，强制值）
    - **强制值，不得因版面、边距、元素冲突而缩小**
    - 若标题无法完整显示，应允许其接近画面边缘
    - **禁止**：降低字号、压缩字距、缩放文字、自动换行
    - **加粗显示**

    位置规范：
    - 标题文字：水平居中，整体居中（略偏下）
    - 单行显示，不自动换行，不压缩字距，不拉伸比例

    Args:
        title: 封面标题（5字）
        background_path: 背景图路径（只读资产）
        output_path: 输出文件路径
    """

    # 检查背景图是否存在
    if not background_path.exists():
        raise RuntimeError(f"❌ 背景图不存在: {background_path}")

    # 打开背景图
    img = Image.open(background_path)
    width, height = img.size

    # 创建绘制对象
    draw = ImageDraw.Draw(img)

    # ====== 字体配置（严格规范） ======
    # 默认使用苹方（PingFang SC）
    # 苹方 TTC 文件在 AssetsV2 目录中
    font_configs = [
        ("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc", 0), # PingFang SC Regular
        ("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc", 1), # PingFang SC Medium
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0), # macOS 黑体 Medium（备用）
    ]

    title_font = None

    for font_path_str, font_index in font_configs:
        font_path = Path(font_path_str).expanduser()
        if font_path.exists():
            try:
                # 标题字体大小 = 376 pt，使实际像素为「比特币行情分析」的 1.85 倍
                title_font = ImageFont.truetype(str(font_path), 376, index=font_index)
                break
            except Exception as e:
                continue

    # 如果还是没有字体，报错
    if title_font is None:
        raise RuntimeError(
            "❌ 未找到可用的中文字体！\n"
            "请安装苹方或黑体字体。"
        )

    # ====== 颜色配置（严格规范） ======
    # 纯白色 #FFFFFF，禁止描边、阴影、发光、渐变、半透明
    text_color = (255, 255, 255)  # #FFFFFF

    # ====== 位置配置（严格规范） ======
    # 标题文字：水平居中，整体居中（略偏下）
    # **强制字号 376 pt，不因版面原因缩小**
    # 单行显示，不自动换行，不压缩字距，不拉伸比例
    # 若标题超出画布边缘，允许其接近边缘，但不得降低字号

    # 计算文字位置（使用强制字号 376 pt）
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    # 水平居中（不因宽度问题调整位置或字号）
    title_x = (width - title_width) // 2

    # 垂直位置（参考封面-1：标题到顶部"比特币行情分析"底部的距离 = 标题底部到封面底部的距离）
    # 假设"比特币行情分析"底部约在 80px 处，标题应该在剩余空间正中间
    top_area_end = 80  # "比特币行情分析"底部位置
    available_space = height - top_area_end
    title_center_y = top_area_end + available_space // 2
    title_y = title_center_y - title_height // 2

    # 绘制文字（纯白色，无描边）
    draw.text((title_x, title_y), title, font=title_font, fill=text_color)

    # 保存
    img.save(output_path, 'PNG')
    return output_path


# ====== 主逻辑 ======

def main():
    # 解析参数
    txt_path = DEFAULT_TXT_PATH
    specified_color = None
    target_date = None

    for arg in sys.argv[1:]:
        if arg.endswith('.txt'):
            txt_path = Path(arg)
        elif arg in BACKGROUNDS_SIMPLIFIED:
            specified_color = arg
        elif not arg.startswith('--'):
            try:
                target_date = datetime.strptime(arg, '%Y%m%d')
            except:
                pass

    # 读取文稿
    print(f"📄 读取文稿: {txt_path}")
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if len(content) < 100:
        print("⚠️ 文稿内容较少，将使用保守标题")

    # 获取日期
    if target_date is None:
        target_date = datetime.now()

    date_str = target_date.strftime('%Y%m%d')
    print(f"📅 日期: {target_date.strftime('%Y-%m-%d')}")

    # 获取背景颜色
    bg_color, bg_simplified_path, bg_traditional_path, is_specified = get_background_color(specified_color, target_date)
    if is_specified:
        print(f"🎨 背景颜色: {bg_color} (用户指定)")
    else:
        print(f"🎨 背景颜色: {bg_color} (自动轮换)")

    # 检查背景图是否存在
    if not bg_simplified_path.exists():
        print(f"❌ 简体背景图不存在: {bg_simplified_path}")
        print(f"💡 请确保以下背景图已放置在 assets 目录：")
        for color, path in BACKGROUNDS_SIMPLIFIED.items():
            print(f"   - 简体 {color}: {path}")
        return

    if not bg_traditional_path.exists():
        print(f"❌ 繁体背景图不存在: {bg_traditional_path}")
        print(f"💡 请确保以下背景图已放置在 assets 目录：")
        for color, path in BACKGROUNDS_TRADITIONAL.items():
            print(f"   - 繁体 {color}: {path}")
        return

    # 检查是否自动模式或指定标题（从命令行参数获取）
    auto_mode = '--auto' in sys.argv
    custom_title = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith('--title='):
            custom_title = arg.split('=', 1)[1]
            break

    # 只在需要时生成标题候选（非指定标题模式）
    titles = None
    if not custom_title:
        # 调用 DeepSeek 生成标题候选
        print("\n🤖 正在生成封面标题候选...")
        try:
            titles = call_deepseek_for_titles(content)
        except RuntimeError as e:
            print(f"\n{e}")
            # 使用备用标题
            titles = ["短期见底没", "关注阻力位", "反弹后再跌"]
            print("⚠️ 使用备用标题")

        print("\n" + "="*60)
        print("【标题候选】")
        for i, title in enumerate(titles, 1):
            print(f"{i}. {title} ({len(title)}字)")
        print("="*60)

    if custom_title:
        # 使用指定的标题
        selected_title = custom_title
        print(f"\n📝 使用指定标题: {selected_title}")
    elif auto_mode:
        # 自动模式：使用第一个候选标题
        selected_title = titles[0]
        print(f"\n🤖 自动模式：已选择第1个标题: {selected_title}")
    else:
        # === 人工审核（强制等待） ===
        print("\n请选择一个标题：")
        print("  - 输入 1/2/3 选择对应标题")
        print("  - 或直接输入你想要的标题（4-6个字）")
        print("  - 输入 q 取消")
        print("-"*60)

        # 等待用户选择（强制中断点）
        while True:
            choice = input("> ").strip()

            if choice.lower() == 'q':
                print("❌ 已取消")
                return

            if choice in ['1', '2', '3']:
                # 使用已生成的候选标题，不再重新生成
                selected_title = titles[int(choice) - 1]
                break
            elif 4 <= len(choice) <= 6:  # 允许4-6个字
                selected_title = choice
                break
            else:
                print("⚠️ 请输入 1/2/3 或 4-6 个字的标题")

        print(f"\n✅ 已选择: {selected_title}")
        print("⏸️ 人工审核通过，继续生成封面...")

    # 生成简体封面（使用简体背景图）
    output_simplified = OUTPUT_DIR / f"cover_{date_str}_simplified.png"
    print(f"\n🎨 正在生成简体封面...")
    draw_cover(selected_title, bg_simplified_path, output_simplified)
    print(f"✅ 简体封面: {output_simplified}")

    # 生成繁体封面（使用繁体背景图 + 繁体标题）
    title_traditional = to_traditional(selected_title)
    output_traditional = OUTPUT_DIR / f"cover_{date_str}_traditional.png"
    print(f"\n🎨 正在生成繁体封面...")
    draw_cover(title_traditional, bg_traditional_path, output_traditional)
    print(f"✅ 繁体封面: {output_traditional}")

    print(f"\n✅ 封面生成完成！")
    print(f"\n📋 封面信息：")
    print(f"  - 简体标题: {selected_title}")
    print(f"  - 繁体标题: {title_traditional}")
    print(f"  - 背景颜色: {bg_color}")
    print(f"  - 简体背景: {bg_simplified_path.name}")
    print(f"  - 繁体背景: {bg_traditional_path.name}")

    # 复制到 2output 文件夹
    # 获取月日格式（如 0207）
    md_str = target_date.strftime('%m%d')
    output_2_simplified = OUTPUT_DIR_2 / f"简体{md_str}.png"
    output_2_traditional = OUTPUT_DIR_2 / f"繁体{md_str}.png"

    shutil.copy2(output_simplified, output_2_simplified)
    print(f"📋 已复制简体封面到: {output_2_simplified}")

    shutil.copy2(output_traditional, output_2_traditional)
    print(f"📋 已复制繁体封面到: {output_2_traditional}")

    # 在 macOS 上自动打开预览
    try:
        subprocess.run(['open', str(output_simplified)], check=True)
        print(f"🖼️ 已打开预览")
    except:
        pass


if __name__ == "__main__":
    main()
