#!/usr/bin/env python3
"""
为币种/股票独立视频生成封面和标题

基于 Video4 字幕，为每个币种/股票视频：
1. 提取对应时间段的字幕内容
2. 生成封面文字（5字）
3. 生成视频标题（80字左右，含前后缀）
4. 生成封面图片
5. 重命名视频文件
"""

import sys
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# 配置
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
SUBTITLE_DIR = "/Users/ai/Documents/video_pipeline/3daily"
OUTPUT_DIR = "/Users/ai/Documents/video_pipeline/2output"
COVER_DIR = "/Users/ai/Documents/video_pipeline/3daily/covers"

# 币种配置（与 generate_coin_videos.py 一致）
COINS = [
    {"name": "以太坊", "start": "00:02:22,560", "end": "00:03:26,240"},
    {"name": "英特尔", "start": "00:03:35,200", "end": "00:04:09,560"},
    {"name": "美光", "start": "00:04:12,600", "end": None},  # 到视频结束
]

def time_to_seconds(time_str):
    """将时间码转换为秒"""
    if ',' in time_str:
        parts = time_str.split(',')
        time_part = parts[0]
        ms = int(parts[1]) / 1000
        h, m, s = map(int, time_part.split(':'))
        return h * 3600 + m * 60 + s + ms
    return 0

def get_latest_subtitle():
    """获取最新的简体字幕"""
    import glob
    srt_pattern = os.path.join(SUBTITLE_DIR, "简体*.srt")
    srt_files = glob.glob(srt_pattern)

    if not srt_files:
        raise RuntimeError(f"❌ 在 {SUBTITLE_DIR} 中未找到简体字幕")

    srt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return srt_files[0]

def parse_srt(srt_path):
    """解析 SRT 字幕文件"""
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

def extract_subtitle_content(subtitles, start_s, end_s):
    """提取指定时间范围的字幕内容"""
    start_ms = int(start_s * 1000)
    end_ms = int(end_s * 1000) if end_s else float('inf')

    content_lines = []
    for start, end, text in subtitles:
        if start >= start_ms and start < end_ms:
            content_lines.append(text)

    return '\n'.join(content_lines)

def call_deepseek(prompt):
    """调用 DeepSeek API"""
    import requests
    from dotenv import load_dotenv

    # 加载 .env 文件
    env_path = "/Users/ai/.claude/skills/ethereum-extract/.env"
    load_dotenv(env_path)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(f"❌ 未找到 DEEPSEEK_API_KEY（已加载 {env_path}）")

    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的金融行情分析师，擅长撰写简洁有力的行情分析标题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    )

    if response.status_code != 200:
        raise RuntimeError(f"❌ DeepSeek API 调用失败: {response.text}")

    result = response.json()
    return result['choices'][0]['message']['content']

def generate_cover_text(content, coin_name):
    """生成封面文字（5字）"""
    prompt = f"""基于以下{coin_name}的行情分析内容，生成5-7个候选封面标题。

**要求**：
1. 必须正好5个字（不能多也不能少）
2. 偏交易、行情、走势判断
3. 不使用营销、夸张、诱导性词汇
4. 不出现违规金融承诺类表述
5. 请生成5-7个候选，确保至少有3个符合要求

**内容**：
{content}

**输出格式**（严格按此格式，不要有其他内容）：
1. 标题1
2. 标题2
3. 标题3
4. 标题4
5. 标题5

**参考风格**：
- 短期见底没
- 反弹后再跌
- 关注82阻力
- Y浪尾声
- 等待反弹"""

    response = call_deepseek(prompt)

    print(f"   📝 DeepSeek 原始响应:\n{response}\n")

    # 解析标题
    titles = []
    for line in response.strip().split('\n'):
        line = line.strip()
        # 移除序号
        match = re.match(r'^\d+[\.\、]\s*(.+)$', line)
        if match:
            title = match.group(1).strip()
        else:
            title = line

        # 只保留正好5个字的标题
        if len(title) == 5:
            titles.append(title)

    print(f"   📝 解析出的5字标题: {titles}")

    if len(titles) < 1:
        # 如果没有5字标题，使用默认标题
        print(f"   ⚠️  未生成5字标题，使用默认标题")
        default_titles = {
            "以太坊": "以太待确认",
            "英特尔": "五浪将完成",
            "美光": "长期上涨中"
        }
        return [default_titles.get(coin_name, "等待确认")]

    # 返回所有有效的标题（至少1个）
    return titles

def generate_video_title(content, coin_name):
    """生成视频标题（80字左右，含前后缀）"""

    # 获取日期
    today = datetime.now()
    month_day = today.strftime("%m.%d")

    prompt = f"""基于以下{coin_name}的行情分析内容，生成一个视频标题。

**要求**：
1. 标题长度：60-80字（含前后缀）
2. 前缀格式："{month_day}{coin_name}价格今日行情："
3. 后缀："（{coin_name}合约交易）军长"
4. 中间部分：几句话总结行情分析要点
5. 保留所有标点符号（冒号、逗号、句号等）

**内容**：
{content}

**输出格式**（严格按此格式，只输出标题，不要有其他内容）：
{month_day}{coin_name}价格今日行情：[分析要点]（{coin_name}合约交易）军长"""

    response = call_deepseek(prompt)

    # 清理响应
    title = response.strip()

    # 移除可能的引号
    title = title.strip('"').strip("'").strip('""').strip("''")

    return title

def generate_cover_image(coin_name, cover_text, output_path):
    """生成封面图片"""
    # 加载背景模板（使用中文文件名）
    bg_path = f"/Users/ai/.claude/skills/generate-cover-v2/assets/简体背景蓝色.png"

    if not os.path.exists(bg_path):
        raise RuntimeError(f"❌ 背景图片不存在: {bg_path}")

    # 打开背景
    img = Image.open(bg_path)
    draw = ImageDraw.Draw(img)

    # 字体设置
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 140)
    except:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 140)

    # 文字位置（居中偏左）
    img_width, img_height = img.size
    text_x = int(img_width * 0.15)
    text_y = int((img_height - 140) / 2)

    # 绘制阴影
    shadow_offset = 4
    draw.text((text_x + shadow_offset, text_y + shadow_offset),
              cover_text, font=font,
              fill=(0, 0, 0, 128))

    # 绘制主文字
    draw.text((text_x, text_y), cover_text,
              font=font, fill=(255, 255, 255, 255))

    # 保存
    img.save(output_path)
    print(f"   ✅ 封面已保存: {output_path}")

def rename_video(old_path, coin_name, video_title):
    """重命名视频文件"""
    # 构建新文件名
    # 清理文件名中的非法字符
    safe_title = video_title
    for char in ['<', '>', '"', '/', '\\', '|', '?', '*']:
        safe_title = safe_title.replace(char, '')

    # 按字节长度截断（保留扩展名）
    filename_bytes = safe_title.encode('utf-8')
    if len(filename_bytes) > 200:
        safe_title = filename_bytes[:200].decode('utf-8', errors='ignore')

    new_name = f"{safe_title}.mp4"
    new_path = os.path.join(os.path.dirname(old_path), new_name)

    # 重命名
    os.rename(old_path, new_path)
    print(f"   ✅ 视频已重命名: {new_name}")

    return new_path

def main():
    print("\n🎨 开始生成封面和标题...\n")

    # 获取字幕文件
    srt_path = get_latest_subtitle()
    print(f"✅ 找到字幕: {srt_path}\n")

    # 解析字幕
    subtitles = parse_srt(srt_path)

    # 获取视频总时长（用于美光的结束时间）
    video4_files = list(Path(OUTPUT_DIR).glob("4字幕*.mp4"))
    if not video4_files:
        raise RuntimeError("❌ 未找到 Video4")

    video4_path = sorted(video4_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    cmd = [FFMPEG_PATH, "-i", str(video4_path), "-hide_banner"]
    result = subprocess.run(cmd, capture_output=True)
    output = result.stderr.decode('utf-8')

    duration_s = 0
    for line in output.split('\n'):
        if 'Duration:' in line:
            match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
            if match:
                h, m, s, ms = match.groups()
                duration_s = ((int(h) * 60 + int(m)) * 60 + int(s)) + int(ms) / 100
                break

    # 处理每个币种
    for coin in COINS:
        coin_name = coin["name"]
        start_s = time_to_seconds(coin["start"])
        end_s = time_to_seconds(coin["end"]) if coin["end"] else duration_s

        print(f"📝 处理 {coin_name}...")
        print(f"   时间范围: {start_s:.2f}s - {end_s:.2f}s")

        # 提取字幕内容
        content = extract_subtitle_content(subtitles, start_s, end_s)
        print(f"   提取到 {len(content)} 字字幕内容")

        if not content:
            print(f"   ⚠️  警告：{coin_name} 无字幕内容，跳过")
            continue

        # 生成封面文字
        print(f"\n   正在生成封面文字...")
        titles = generate_cover_text(content, coin_name)
        print(f"   ✅ 生成3个候选：")
        for i, title in enumerate(titles, 1):
            print(f"      {i}. {title}")

        # 选择第一个标题
        cover_text = titles[0]
        print(f"\n   ✅ 选中封面文字: {cover_text}")

        # 生成视频标题
        print(f"\n   正在生成视频标题...")
        video_title = generate_video_title(content, coin_name)
        print(f"   ✅ 视频标题: {video_title}")

        # 重命名视频文件
        print(f"\n   正在重命名视频文件...")
        old_video_path = os.path.join(OUTPUT_DIR, f"06.12{coin_name}.mp4")
        if os.path.exists(old_video_path):
            new_video_path = rename_video(old_video_path, coin_name, video_title)
        else:
            print(f"   ⚠️  警告：视频文件不存在: {old_video_path}")

        print(f"\n✅ {coin_name} 处理完成！\n")
        print("-" * 80)

    print(f"\n✅ 所有封面和标题生成完成！")

if __name__ == "__main__":
    main()
